from datetime import datetime, date
from typing import List, Any, Union, Optional
from fastapi import HTTPException
from app.models.schemas.ingestion import IngestionRequest
from app.agents.classifier_agent import classify_text
from app.agents.extractor_agent import extract_data
from app.models.domain.core_entities import Client, Project
# Consolidated Project-Scoped Models
from app.models.domain.sections import (
    UniversalContext, OperationsState, TechnicalState, CommercialState,
    StrategyState, MarketingState, MiscState,
    Task, Interaction, TechItem, Goal, StakeholderInfo
)
from app.models.domain.document_references import ClientStakeholder, InternalStakeholder, ProjectAssignment
from app.services.vector_store import vector_store
from app.services.context_manager import context_manager
from app.core.logging_config import logger

async def process_text_upload(request: IngestionRequest):
    logger.info(f"Starting ingestion process for source: {request.source_type}")
    text_content = request.text or ""
    
    extracted_data = {}
    section_id = 0 # Default to unknown/fail safe
    
    # 0. Context Management (Pre-fetch for context-aware extraction)
    client = await context_manager.get_or_create_client(request.client_id) if request.client_id else None
    if not client:
        raise HTTPException(status_code=400, detail="Cannot ingest data without a valid Client context.")

    project = None
    if request.project_id:
        project = await context_manager.get_or_create_project(request.project_id, client)
    else:
        project = await context_manager.get_or_create_project(f"General-{client.name}", client)

    try:
        # 1. Classify with Retry Logic
        import asyncio
        retries = 3
        # ... (retry logic same as before)
        for attempt in range(retries):
            try:
                section_id = await classify_text(text_content)
                break
            except Exception as e:
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = (2 ** attempt) * 2 # 2s, 4s, 8s
                    logger.warning(f"Rate Limit 429. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise e
        
        # 2. Identify existing state to pass as context
        existing_doc = None
        # We need to know section_id first, so we'll do this inside the classify block or after
        # Let's move classify up.
        
        # 1. Classify (First)
        for attempt in range(retries):
            # ... (classify_text call)
            pass # placeholder for logic below
        
        # NOTE: Refactoring flow to call classify THEN fetch THEN extract
    except Exception as e:
        # ...
        pass
        
    # --- UPDATED FLOW ---
    try:
        section_id = await classify_text(text_content)
        
        # Map section_id to model class
        model_map = {
            1: UniversalContext, 2: OperationsState, 3: TechnicalState,
            4: CommercialState, 5: StrategyState, 6: MarketingState, 7: MiscState
        }
        model_class = model_map.get(section_id)
        
        # Fetch existing state
        existing_doc = await model_class.find_one(model_class.project.id == project.id) if model_class else None
        existing_json = None
        if existing_doc:
            # mode='json' ensures ObjectIds and Datetimes are converted to strings
            existing_json = existing_doc.model_dump(mode='json', exclude={"id", "_id", "project", "last_updated", "sources"})
        
        # 2. Extract with Context
        extracted_data = await extract_data(text_content, section_id, existing_context=existing_json)
        logger.info(f"Data merged/extracted for Project {project.name} Section {section_id}")
        
    except Exception as e:
        logger.error(f"LLM/Context Error: {e}")
        return {"status": "failed", "reason": str(e)}

    # 3. Save / Update (Strict One-Per-Project)
    if not existing_doc and model_class:
        existing_doc = model_class(project=project)
        await existing_doc.insert()
        
    # Apply extracted data to doc
    if existing_doc and extracted_data:
        # Update fields dynamically
        for key, value in extracted_data.items():
            if value is not None and hasattr(existing_doc, key):
                target_val = getattr(existing_doc, key)
                # If target is a list but value is a dict, wrap it
                if isinstance(target_val, list) and isinstance(value, dict):
                    setattr(existing_doc, key, [value])
                else:
                    setattr(existing_doc, key, value)
        
        existing_doc.last_updated = datetime.utcnow()
        
        # Track Provenance
        if hasattr(existing_doc, "sources"):
            from app.models.domain.document_references import DocumentSource
            source_info = DocumentSource(
                source_type=request.source_type or "manual",
                source_title=f"Extracted from {request.source_type}" if request.source_type else "Direct Injection",
                source_date=datetime.utcnow()
            )
            existing_doc.sources.append(source_info)
            
        await existing_doc.save()
        saved_objects = [existing_doc]
    else:
        saved_objects = []
         
    # 7. Finalize & Embed (Simplified)
    ids = [str(o.id) for o in saved_objects]
    for saved_id in ids:
        try:
            vector_store.add_documents(
                documents=[text_content],
                metadatas=[{
                    "client_id": str(client.id) if client else "unknown",
                    "project_id": str(project.id) if project else "unknown",
                    "section_id": section_id,
                    "mongo_id": saved_id,
                    "timestamp": datetime.utcnow().isoformat()
                }],
                ids=[f"vec_{saved_id}"]
            )
        except Exception as e:
            logger.error(f"Vector Store Error: {e}")
    
    if saved_objects:
        await _sync_external_stakeholders(project, section_id, extracted_data)
    
    return {
        "status": "success", "section_id": section_id,
        "extracted": extracted_data, "saved_ids": ids,
        "context": {"client_id": str(client.id) if client else None}
    }

async def _sync_external_stakeholders(project: Project, section_id: int, data: dict):
    """Sync extracted stakeholder data to the dedicated ExternalStakeholder collection"""
    from app.models.domain.document_references import ExternalStakeholder
    
    stakeholders_to_process = []
    
    if section_id == 1:
        # POCs from Section 1
        pocs = data.get("pocs", [])
        if isinstance(pocs, list):
            for p in pocs:
                if isinstance(p, dict) and p.get("name"):
                    p["category"] = "POC"
                    stakeholders_to_process.append(p)
                    
    elif section_id == 5:
        # Stakeholder map from Section 5
        sh_map = data.get("stakeholder_map", [])
        if isinstance(sh_map, list):
            for s in sh_map:
                if isinstance(s, dict) and s.get("name"):
                    s["category"] = "Decision Maker" if "Decision" in s.get("role", "") else "Influencer"
                    stakeholders_to_process.append(s)

    for sh in stakeholders_to_process:
        try:
            # Upsert by project and name
            existing = await ExternalStakeholder.find_one(
                ExternalStakeholder.project.id == project.id,
                ExternalStakeholder.name == sh["name"]
            )
            
            if existing:
                existing.role = sh.get("role", existing.role)
                existing.email = sh.get("email", existing.email)
                existing.phone = sh.get("phone", existing.phone)
                existing.sentiment = sh.get("sentiment", existing.sentiment)
                existing.influence = sh.get("influence", existing.influence)
                existing.category = sh.get("category", existing.category)
                existing.last_updated = datetime.utcnow()
                await existing.save()
            else:
                new_sh = ExternalStakeholder(
                    project=project,
                    name=sh["name"],
                    role=sh.get("role", "Unknown"),
                    category=sh.get("category", "General"),
                    email=sh.get("email"),
                    phone=sh.get("phone"),
                    sentiment=sh.get("sentiment", "Neutral"),
                    influence=sh.get("influence", "Medium")
                )
                await new_sh.insert()
        except Exception as e:
            logger.error(f"Error syncing stakeholder {sh.get('name')}: {e}")
