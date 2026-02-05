from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional
from app.services.ingestion.watchdog import watchdog
from app.services.ingestion.chunker import chunker
from app.services.ingestion.vector_store import vector_store
from app.services.ingestion.basecamp import basecamp_service
from app.services.automation.startup_automation import startup_automation
from app.services.rag.query_service import rag_service
from app.services.intelligence.agents.reducer import reducer
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.memory_adapters import msg_queue
import logging

router = APIRouter()

@router.post("/sync")
async def trigger_manual_sync(current_user: User = Depends(get_current_user)) -> Any:
    """
    Manually trigger a sync cycle across all pollers (Local, Gmail, Drive).
    """
    try:
        logging.info(f"Manual sync triggered by {current_user.email}")
        await watchdog.trigger_sync()
        return {"status": "Sync cycle triggered successfully"}
    except Exception as e:
        logging.error(f"Manual sync failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger sync cycle")


@router.post("/basecamp/sync/{project_id}")
@router.post("/basecamp/sync")
async def trigger_basecamp_sync(
    project_id: Optional[str] = None,
    full_sync: bool = False,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Trigger Basecamp sync for a specific project or all projects.
    
    - project_id: Optional project to sync
    - full_sync=false (default): Only fetch new data since last sync
    - full_sync=true: Fetch all data (reset sync state)
    """
    logging.info(f"🚀 === BASECAMP SYNC ENDPOINT TRIGGERED ===")
    logging.info(f"👤 User: {current_user.email}")
    logging.info(f"🔄 Full sync: {full_sync}")
    
    try:
        if not basecamp_service.enabled:
            logging.error("❌ Basecamp not configured")
            raise HTTPException(status_code=400, detail="Basecamp not configured")
        
        logging.info(f"Basecamp sync triggered by {current_user.email} (project={project_id}, full={full_sync})")
        
        if full_sync:
            await basecamp_service.reset_sync_state(project_id)
        
        # If project_id is provided, we only want to sync that one
        if project_id:
            # We use the internal export_project method to sync just one
            async with httpx.AsyncClient() as client:
                export_data = await basecamp_service.export_project(client, project_id, full_sync=full_sync)
                if export_data and export_data.get("_metadata"):
                    text_content = basecamp_service.convert_to_text(export_data)
                    meta = export_data.get("_metadata", {})
                    results = {
                        "successful": [project_id],
                        "failed": [],
                        "documents": [{
                            "project_id": project_id,
                            "project_name": meta.get("project_name", project_id),
                            "content": text_content,
                            "metadata": meta
                        }]
                    }
                else:
                    results = {"successful": [], "failed": [project_id], "documents": []}
        else:
            results = await basecamp_service.sync_all_projects(full_sync=full_sync)
        
        # Queue documents for RAG/embedding pipeline
        docs_queued = 0
        for doc in results.get("documents", []):
            try:
                await msg_queue.enqueue({
                    "filename": f"basecamp_{doc['project_id']}.txt",
                    "content": doc["content"],
                    "client_id": "basecamp",
                    "project_id": doc["project_id"],
                    "source": "basecamp"
                })
                docs_queued += 1
                logging.info(f"📄 Queued document for project: {doc['project_id']}")
            except Exception as e:
                logging.error(f"❌ Failed to queue document for {doc['project_id']}: {e}")
        
        # TRIGGER COMPREHENSIVE EXTRACTION FOR ALL SOURCES
        logging.info("🧠 === TRIGGERING COMPREHENSIVE EXTRACTION FOR ALL SOURCES ===")
        
        extraction_results = []
        for doc in results.get("documents", []):
            project_id = doc["project_id"]
            project_name = doc.get("project_name", project_id)
            
            try:
                logging.info(f"🔍 Starting comprehensive extraction for: {project_name}")
                
                # Import here to avoid circular imports
                from app.services.rag.query_service import rag_service
                from app.services.intelligence.agents.reducer import reducer
                
                # Extract using project_name for cross-source matching
                agent_outputs = await rag_service.extract_all_sections(
                    client_id="basecamp",
                    project_id=project_id,
                    project_name=project_name
                )
                
                if agent_outputs:
                    # Persist the extracted data
                    state = {
                        "metadata": {
                            "client_id": "basecamp",
                            "project_id": project_id,
                            "project_name": project_name,
                            "filename": f"manual_extraction_{project_id}",
                            "extraction_type": "comprehensive_multi_source",
                            "triggered_by": "manual_sync",
                            "user": current_user.email
                        },
                        **agent_outputs
                    }
                    
                    reduction_result = await reducer.reduce_and_persist(state)
                    
                    extraction_results.append({
                        "project_id": project_id,
                        "project_name": project_name,
                        "sections_extracted": list(agent_outputs.keys()),
                        "fields_updated": reduction_result.get("fields_updated", 0),
                        "status": "success"
                    })
                    
                    logging.info(f"✅ Comprehensive extraction completed for {project_name}")
                    logging.info(f"   📊 Sections: {list(agent_outputs.keys())}")
                    logging.info(f"   📝 Fields updated: {reduction_result.get('fields_updated', 0)}")
                    
                else:
                    logging.warning(f"⚠️ No data extracted for {project_name}")
                    extraction_results.append({
                        "project_id": project_id,
                        "project_name": project_name,
                        "status": "no_data"
                    })
                    
            except Exception as e:
                logging.error(f"❌ Comprehensive extraction failed for {project_name}: {e}")
                extraction_results.append({
                    "project_id": project_id,
                    "project_name": project_name,
                    "status": "error",
                    "error": str(e)
                })
        
        successful_extractions = len([r for r in extraction_results if r["status"] == "success"])
        failed_extractions = len([r for r in extraction_results if r["status"] == "error"])
        
        response = {
            "status": "success",
            "sync_type": "full" if full_sync else "incremental",
            "successful_projects": results.get("successful", []),
            "failed_projects": results.get("failed", []),
            "documents_queued": docs_queued,
            "extraction_results": {
                "successful": successful_extractions,
                "failed": failed_extractions,
                "details": extraction_results
            },
            "comprehensive_extraction": True
        }
        
        logging.info(f"🎉 === BASECAMP SYNC COMPLETE ===")
        logging.info(f"✅ Successful projects: {len(response['successful_projects'])}")
        logging.info(f"❌ Failed projects: {len(response['failed_projects'])}")
        logging.info(f"📄 Documents queued: {response['documents_queued']}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"❌ Basecamp sync failed with unexpected error: {e}")
        import traceback
        logging.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/basecamp/status")
async def get_basecamp_status(current_user: User = Depends(get_current_user)) -> Any:
    """Get Basecamp integration status and last sync times."""
    logging.info(f"🔍 === BASECAMP STATUS CHECK ===")
    logging.info(f"👤 User: {current_user.email}")
    
    try:
        sync_states = {}
        for pid in basecamp_service.project_ids:
            last_sync = await basecamp_service.get_last_sync_time(pid)
            sync_states[pid] = last_sync.isoformat() if last_sync else None
        
        status = {
            "enabled": basecamp_service.enabled,
            "account_id": basecamp_service.account_id,
            "project_ids": basecamp_service.project_ids,
            "last_syncs": sync_states
        }
        
        logging.info(f"📊 Status: Enabled={status['enabled']}, Projects={len(status['project_ids'])}")
        return status
        
    except Exception as e:
        logging.error(f"❌ Error getting Basecamp status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/basecamp/reset")
async def reset_basecamp_sync(
    project_id: str = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Reset sync state (forces full sync on next run)."""
    await basecamp_service.reset_sync_state(project_id)
    return {"status": "reset", "project_id": project_id or "all"}



@router.post("/ingest")
async def ingest_document(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Phase 1: Ingest a document into the vector store.
    Chunks the text, embeds it, and stores in ChromaDB.
    
    Payload format: {
        "text": "...",
        "metadata": {"project_id": "...", "client_id": "...", "filename": "..."}
    }
    """
    text = payload.get("text")
    metadata = payload.get("metadata", {})
    
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' in payload")
    
    client_id = metadata.get("client_id", "unknown")
    project_id = metadata.get("project_id", "default")
    
    try:
        logging.info(f"Ingesting document for {client_id}/{project_id} by {current_user.email}")
        
        # 1. Chunk the document
        chunks = chunker.chunk_document(text, metadata)
        
        # 2. Store in vector database
        num_chunks = await vector_store.add_chunks(chunks, client_id, project_id)
        
        return {
            "status": "success",
            "project_id": project_id,
            "client_id": client_id,
            "chunks_stored": num_chunks,
            "filename": metadata.get("filename", "unknown")
        }
        
    except Exception as e:
        logging.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


@router.post("/ingest-batch")
async def ingest_batch(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Ingest multiple documents at once.
    
    Payload format: {
        "documents": [
            {"text": "...", "metadata": {"filename": "..."}},
            ...
        ],
        "client_id": "...",
        "project_id": "..."
    }
    """
    documents = payload.get("documents", [])
    client_id = payload.get("client_id", "unknown")
    project_id = payload.get("project_id", "default")
    
    if not documents:
        raise HTTPException(status_code=400, detail="Missing 'documents' in payload")
    
    try:
        logging.info(f"Batch ingesting {len(documents)} docs for {client_id}/{project_id}")
        
        total_chunks = 0
        for doc in documents:
            text = doc.get("text", "")
            metadata = {**doc.get("metadata", {}), "client_id": client_id, "project_id": project_id}
            
            if text:
                chunks = chunker.chunk_document(text, metadata)
                total_chunks += await vector_store.add_chunks(chunks, client_id, project_id)
        
        return {
            "status": "success",
            "project_id": project_id,
            "client_id": client_id,
            "documents_processed": len(documents),
            "total_chunks_stored": total_chunks
        }
        
    except Exception as e:
        logging.error(f"Batch ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch ingestion error: {str(e)}")


@router.post("/extract")
async def extract_all(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Phase 2: Extract data from ingested documents using RAG.
    Runs all agents with section-specific context retrieval.
    
    Payload format: {
        "client_id": "...",
        "project_id": "...",
        "project_name": "..." (optional - for multi-source extraction)
    }
    """
    client_id = payload.get("client_id")
    project_id = payload.get("project_id")
    project_name = payload.get("project_name")  # Add project_name support
    
    if not client_id or not project_id:
        raise HTTPException(status_code=400, detail="Missing 'client_id' or 'project_id'")
    
    try:
        logging.info(f"RAG extraction for {client_id}/{project_id} by {current_user.email}")
        if project_name:
            logging.info(f"Using project_name for multi-source extraction: {project_name}")
        
        # 1. Run RAG extraction for all sections with project_name
        agent_outputs = await rag_service.extract_all_sections(client_id, project_id, project_name)
        
        # 2. Merge outputs into state and persist via Reducer
        state = {
            "metadata": {"client_id": client_id, "project_id": project_id, "filename": "rag_extraction"},
            **agent_outputs
        }
        
        result = await reducer.reduce_and_persist(state)
        
        return {
            "status": "success",
            "project_id": project_id,
            "client_id": client_id,
            "sections_extracted": list(agent_outputs.keys()),
            "fields_updated": result.get("fields_updated", 0)
        }
        
    except Exception as e:
        logging.error(f"RAG extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


@router.post("/process")
async def process_document(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Combined: Ingest + Extract in one call.
    For backward compatibility and simple use cases.
    
    Payload format: {
        "text": "...",
        "metadata": {"project_id": "...", "client_id": "...", "filename": "..."}
    }
    """
    text = payload.get("text")
    metadata = payload.get("metadata", {})
    
    if not text or not metadata:
        raise HTTPException(status_code=400, detail="Missing 'text' or 'metadata' in payload")
    
    client_id = metadata.get("client_id", "unknown")
    project_id = metadata.get("project_id", "default")
    
    try:
        logging.info(f"Processing (ingest+extract) for {client_id}/{project_id}")
        
        # 1. Ingest: Chunk and store
        chunks = chunker.chunk_document(text, metadata)
        num_chunks = await vector_store.add_chunks(chunks, client_id, project_id)
        logging.info(f"Stored {num_chunks} chunks for {metadata.get('filename', 'unknown')}")
        
        # 2. NOTE: We don't extract immediately for each doc.
        # The idea is to ingest ALL docs first, then call /extract once.
        # This allows cross-document context retrieval.
        
        return {
            "status": "ingested",
            "project_id": project_id,
            "client_id": client_id,
            "chunks_stored": num_chunks,
            "filename": metadata.get("filename", "unknown"),
            "message": "Document ingested. Call /extract after all documents are uploaded."
        }
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.delete("/clear/{client_id}/{project_id}")
async def clear_project_vectors(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete all vectors for a project."""
    try:
        deleted = vector_store.delete_project(client_id, project_id)
        return {"status": "success", "chunks_deleted": deleted}
    except Exception as e:
        logging.error(f"Clear failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/startup/status")
async def get_startup_automation_status() -> Any:
    """Get current sync status for all automation sources (no auth required)."""
    try:
        status = await startup_automation.get_sync_status()
        return status
    except Exception as e:
        logging.error(f"Failed to get startup automation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/startup/check")
async def trigger_startup_automation_check() -> Any:
    """Manually trigger startup automation check (no auth required)."""
    try:
        logging.info("Startup automation check manually triggered")
        results = await startup_automation.check_and_run_automation()
        return results
    except Exception as e:
        logging.error(f"Manual startup automation check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
