"""
Startup Automation Service

Checks MongoDB for last sync times and automatically triggers sync
if data is older than 24 hours when server starts.
"""

import logging
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from app.services.ingestion.basecamp import basecamp_service
from app.services.ingestion.watchdog import watchdog
from app.core.memory_adapters import msg_queue
from app.core.config import settings


class StartupAutomation:
    """Service to handle startup automation checks."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_and_run_automation(self) -> Dict[str, any]:
        """
        Check if any data sources need syncing and run automation if needed.
        
        Returns:
            Dict with results of what was triggered
        """
        results = {
            "basecamp_triggered": False,
            "watchdog_triggered": False,
            "basecamp_results": None,
            "watchdog_results": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            self.logger.info("=" * 80)
            self.logger.info("🚀 STARTUP AUTOMATION CHECK INITIATED")
            self.logger.info("=" * 80)
            self.logger.info(f"🔧 Configuration: ENABLE_STARTUP_AUTOMATION={settings.ENABLE_STARTUP_AUTOMATION}")

            if not settings.ENABLE_STARTUP_AUTOMATION:
                self.logger.info("🚫 Startup automation is globally disabled in settings")
                self.logger.info("=" * 80)
                return results

            # Ensure database is available
            try:
                from app.core.database import get_database
                db = await get_database()
                self.logger.info("✅ Database connection verified for startup automation")
            except Exception as e:
                self.logger.error(f"❌ Database connection failed: {e}")
                results["error"] = f"Database connection failed: {str(e)}"
                return results

            # Check Basecamp sync status
            self.logger.info("📋 CHECKING BASECAMP STATUS...")
            self.logger.info(f"🔧 Basecamp Config: ENABLE_BASECAMP={settings.ENABLE_BASECAMP}, Service Enabled={basecamp_service.enabled}")
            self.logger.info(f"📦 Basecamp Projects: {basecamp_service.project_ids}")
            
            if settings.ENABLE_BASECAMP and basecamp_service.enabled:
                basecamp_needs_sync = await self._check_basecamp_needs_sync()
                self.logger.info(f"🔍 Basecamp Sync Decision: {basecamp_needs_sync}")
                
                if basecamp_needs_sync:
                    self.logger.info("🚀 BASECAMP DATA OLDER THAN 24H - TRIGGERING STARTUP SYNC")
                    self.logger.info("⏳ Starting Basecamp sync process...")
                    results["basecamp_triggered"] = True
                    results["basecamp_results"] = await self._run_basecamp_sync()
                    
                    # Log sync results
                    if results["basecamp_results"].get("error"):
                        self.logger.error(f"❌ Basecamp sync failed: {results['basecamp_results']['error']}")
                    else:
                        success_count = len(results["basecamp_results"].get("successful_projects", []))
                        failed_count = len(results["basecamp_results"].get("failed_projects", []))
                        docs_queued = results["basecamp_results"].get("documents_queued", 0)
                        
                        self.logger.info(f"✅ Basecamp sync completed:")
                        self.logger.info(f"   📈 Successful projects: {success_count}")
                        self.logger.info(f"   ❌ Failed projects: {failed_count}")
                        self.logger.info(f"   📄 Documents queued: {docs_queued}")
                        
                        if results["basecamp_results"].get("project_names"):
                            self.logger.info("📋 Project names synced:")
                            for pid, name in results["basecamp_results"]["project_names"].items():
                                self.logger.info(f"   - {pid}: {name}")
                else:
                    self.logger.info("✅ Basecamp data is recent - no startup sync needed")
            else:
                self.logger.info("⏭️  Skipping Basecamp Check (Disabled or Service Invalid)")
            
            # Check watchdog sources (local files, Gmail, Drive)
            self.logger.info("📋 CHECKING WATCHDOG SOURCES...")
            watchdog_enabled = any([settings.ENABLE_GMAIL, settings.ENABLE_DRIVE, settings.ENABLE_LOCAL_FILES])
            self.logger.info(f"🔧 Watchdog Config: Gmail={settings.ENABLE_GMAIL}, Drive={settings.ENABLE_DRIVE}, Local={settings.ENABLE_LOCAL_FILES}")
            
            if watchdog_enabled:
                watchdog_needs_sync = await self._check_watchdog_needs_sync()
                self.logger.info(f"🔍 Watchdog Sync Decision: {watchdog_needs_sync}")
                
                if watchdog_needs_sync:
                    self.logger.info("🚀 WATCHDOG SOURCES NEED SYNC - TRIGGERING STARTUP SYNC")
                    results["watchdog_triggered"] = True
                    results["watchdog_results"] = await self._run_watchdog_sync()
                    
                    if results["watchdog_results"].get("error"):
                        self.logger.error(f"❌ Watchdog sync failed: {results['watchdog_results']['error']}")
                    else:
                        self.logger.info("✅ Watchdog sync completed successfully")
                else:
                    self.logger.info("✅ Watchdog sources are recent - no startup sync needed")
            else:
                self.logger.info("⏭️  Skipping Watchdog Check (All sources disabled)")
            
            self.logger.info("=" * 80)
            self.logger.info("🏁 STARTUP AUTOMATION CHECK COMPLETED")
            self.logger.info(f"📊 Summary: Basecamp={results['basecamp_triggered']}, Watchdog={results['watchdog_triggered']}")
            self.logger.info("=" * 80)
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Startup automation failed: {e}")
            self.logger.error(f"📍 Error occurred at: {datetime.now(timezone.utc).isoformat()}")
            import traceback
            self.logger.error(f"❌ Startup automation traceback: {traceback.format_exc()}")
            results["error"] = str(e)
            return results
    
    async def _check_basecamp_needs_sync(self) -> bool:
        """Check if any Basecamp project needs sync (older than 24 hours)."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            self.logger.info(f"🕐 Sync cutoff time: {cutoff_time.isoformat()}")
            
            projects_needing_sync = []
            
            for project_id in basecamp_service.project_ids:
                last_sync = await basecamp_service.get_last_sync_time(project_id)
                self.logger.info(f"📋 Project {project_id}:")
                self.logger.info(f"   Last Sync: {last_sync}")
                self.logger.info(f"   Cutoff: {cutoff_time}")
                
                # If never synced or last sync is older than 24 hours
                if not last_sync:
                    self.logger.info(f"   ⚠️  Never synced - NEEDS SYNC")
                    projects_needing_sync.append(project_id)
                    continue
                    
                # Ensure timezone awareness for comparison
                if last_sync.tzinfo is None:
                    last_sync = last_sync.replace(tzinfo=timezone.utc)
                
                if last_sync < cutoff_time:
                    hours_old = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
                    self.logger.info(f"   ⚠️  Sync is {hours_old:.1f} hours old - NEEDS SYNC")
                    projects_needing_sync.append(project_id)
                else:
                    hours_old = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
                    self.logger.info(f"   ✅ Sync is {hours_old:.1f} hours old - UP TO DATE")
            
            if projects_needing_sync:
                self.logger.info(f"📊 Projects needing sync: {len(projects_needing_sync)}/{len(basecamp_service.project_ids)}")
                self.logger.info(f"   📋 {projects_needing_sync}")
                return True
            else:
                self.logger.info(f"📊 All {len(basecamp_service.project_ids)} Basecamp projects are up to date")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking Basecamp sync status: {e}")
            return False
    
    async def _check_watchdog_needs_sync(self) -> bool:
        """Check if watchdog sources need sync (older than 24 hours)."""
        try:
            # Get database connection to check last sync times
            from app.core.database import get_database
            db = await get_database()
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Check various source collections for last sync
            sources_to_check = []
            if settings.ENABLE_GMAIL:
                sources_to_check.append("gmail_sync_state")
            if settings.ENABLE_DRIVE:
                sources_to_check.append("drive_sync_state")
            if settings.ENABLE_LOCAL_FILES:
                sources_to_check.append("local_files_sync_state")
            
            for source_collection in sources_to_check:
                try:
                    # Get the most recent sync record for this source
                    last_sync_record = await db[source_collection].find_one(
                        sort=[("last_sync", -1)]
                    )
                    
                    if last_sync_record and last_sync_record.get("last_sync"):
                        last_sync = datetime.fromisoformat(
                            last_sync_record["last_sync"].replace("Z", "+00:00")
                        )
                        if last_sync < cutoff_time:
                            self.logger.info(f"Source {source_collection} needs sync (last: {last_sync})")
                            return True
                    else:
                        # No sync record found, needs initial sync
                        self.logger.info(f"Source {source_collection} has no sync record, needs initial sync")
                        return True
                        
                except Exception as e:
                    self.logger.warning(f"Error checking {source_collection}: {e}")
                    # If we can't check, assume it needs sync to be safe
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking watchdog sync status: {e}")
            return False
    
    async def _run_basecamp_sync(self) -> Dict[str, any]:
        """Run Basecamp sync and queue documents for processing with project names."""
        try:
            self.logger.info("🚀 STARTING BASECAMP SYNC PROCESS")
            self.logger.info("=" * 60)
            
            results = await basecamp_service.sync_all_projects()
            
            self.logger.info("📊 BASECAMP SYNC RESULTS:")
            self.logger.info(f"   📈 Successful projects: {len(results.get('successful', []))}")
            self.logger.info(f"   ❌ Failed projects: {len(results.get('failed', []))}")
            self.logger.info(f"   📄 Total documents: {len(results.get('documents', []))}")
            
            # Queue documents for RAG processing with project names
            documents_queued = 0
            for doc in results.get("documents", []):
                project_id = doc["project_id"]
                project_name = doc.get("project_name", project_id)
                
                self.logger.info(f"📄 Processing document for project {project_id} ({project_name})")
                
                content = doc["content"]
                if isinstance(content, str):
                    content = content.encode("utf-8")
                    
                # Enhanced metadata with project name
                metadata = {
                    "filename": f"basecamp_{doc['project_id']}.txt",
                    "client_id": "basecamp",
                    "project_id": doc["project_id"],
                    "project_name": doc.get("project_name", doc["project_id"]),  # Add project name
                    "source": "basecamp",
                    "sync_type": "startup_automation",
                    "items_fetched": doc.get("metadata", {}).get("items_fetched", {}),
                    "exported_at": doc.get("metadata", {}).get("exported_at")
                }
                
                self.logger.info(f"   📋 Filename: {metadata['filename']}")
                self.logger.info(f"   📊 Items fetched: {metadata['items_fetched']}")
                self.logger.info(f"   🕐 Exported at: {metadata['exported_at']}")
                    
                await msg_queue.enqueue({
                    "filename": metadata["filename"],
                    "content": content,
                    "client_id": metadata["client_id"],
                    "project_id": metadata["project_id"],
                    "project_name": metadata["project_name"],  # Include project name
                    "source": metadata["source"],
                    "metadata": metadata  # Full metadata for processing
                })
                documents_queued += 1
                self.logger.info(f"   ✅ Document queued successfully")
            
            self.logger.info("=" * 60)
            self.logger.info("✅ BASECAMP SYNC COMPLETED")
            self.logger.info(f"📊 Summary:")
            self.logger.info(f"   📈 Successful: {len(results.get('successful', []))}")
            self.logger.info(f"   ❌ Failed: {len(results.get('failed', []))}")
            self.logger.info(f"   📄 Documents queued: {documents_queued}")
            
            if results.get("successful"):
                self.logger.info(f"   ✅ Successful projects: {results['successful']}")
            
            if results.get("failed"):
                self.logger.warning(f"   ❌ Failed projects: {results['failed']}")
            
            # TRIGGER COMPREHENSIVE EXTRACTION FOR ALL SOURCES
            self.logger.info("=" * 60)
            self.logger.info("🧠 TRIGGERING COMPREHENSIVE EXTRACTION FOR ALL SOURCES")
            self.logger.info("=" * 60)
            
            extraction_results = []
            
            # Extract for each successfully synced project using project names
            for doc in results.get("documents", []):
                project_id = doc["project_id"]
                project_name = doc.get("project_name", project_id)
                
                try:
                    self.logger.info(f"🔍 Starting extraction for: {project_name} (ID: {project_id})")
                    
                    # Use RAG service to extract from ALL sources (not just Basecamp)
                    from app.services.rag.query_service import rag_service
                    
                    # Extract using project_name for cross-source matching
                    agent_outputs = await rag_service.extract_all_sections(
                        client_id="basecamp",  # This is just for logging, actual search uses project_name
                        project_id=project_id,
                        project_name=project_name  # This enables cross-source matching
                    )
                    
                    if agent_outputs:
                        # Persist the extracted data using the reducer
                        from app.services.intelligence.agents.reducer import reducer
                        
                        state = {
                            "metadata": {
                                "client_id": "basecamp",
                                "project_id": project_id,
                                "project_name": project_name,
                                "filename": f"multi_source_extraction_{project_id}",
                                "extraction_type": "comprehensive_multi_source",
                                "triggered_by": "startup_automation"
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
                        
                        self.logger.info(f"✅ Extraction completed for {project_name}")
                        self.logger.info(f"   📊 Sections: {list(agent_outputs.keys())}")
                        self.logger.info(f"   📝 Fields updated: {reduction_result.get('fields_updated', 0)}")
                        
                    else:
                        self.logger.warning(f"⚠️ No data extracted for {project_name}")
                        extraction_results.append({
                            "project_id": project_id,
                            "project_name": project_name,
                            "status": "no_data"
                        })
                        
                except Exception as e:
                    self.logger.error(f"❌ Extraction failed for {project_name}: {e}")
                    import traceback
                    self.logger.error(f"❌ Extraction traceback: {traceback.format_exc()}")
                    extraction_results.append({
                        "project_id": project_id,
                        "project_name": project_name,
                        "status": "error",
                        "error": str(e)
                    })
            
            self.logger.info("=" * 60)
            self.logger.info("🎯 COMPREHENSIVE EXTRACTION COMPLETED")
            self.logger.info(f"📊 Extraction Summary:")
            
            successful_extractions = [r for r in extraction_results if r["status"] == "success"]
            failed_extractions = [r for r in extraction_results if r["status"] == "error"]
            no_data_extractions = [r for r in extraction_results if r["status"] == "no_data"]
            
            self.logger.info(f"   ✅ Successful extractions: {len(successful_extractions)}")
            self.logger.info(f"   ❌ Failed extractions: {len(failed_extractions)}")
            self.logger.info(f"   ⚠️ No data extractions: {len(no_data_extractions)}")
            
            if successful_extractions:
                total_fields = sum(r.get("fields_updated", 0) for r in successful_extractions)
                self.logger.info(f"   📝 Total fields updated: {total_fields}")
            
            self.logger.info("=" * 60)
            
            return {
                "successful_projects": results.get("successful", []),
                "failed_projects": results.get("failed", []),
                "documents_queued": documents_queued,
                "sync_type": "incremental",
                "project_names": {doc["project_id"]: doc.get("project_name") for doc in results.get("documents", [])},
                "extraction_results": extraction_results,
                "comprehensive_extraction": True
            }
            
        except Exception as e:
            self.logger.error(f"❌ Basecamp startup sync failed: {e}")
            self.logger.error(f"📍 Error occurred at: {datetime.now(timezone.utc).isoformat()}")
            return {"error": str(e)}
    
    async def _run_watchdog_sync(self) -> Dict[str, any]:
        """Run watchdog sync for all sources."""
        try:
            await watchdog.trigger_sync()
            return {"status": "success", "message": "Watchdog sync triggered"}
        except Exception as e:
            self.logger.error(f"Watchdog startup sync failed: {e}")
            return {"error": str(e)}
    
    async def get_sync_status(self) -> Dict[str, any]:
        """Get current sync status for all sources including embedding status."""
        status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "basecamp": {},
            "watchdog_sources": {},
            "embedding_status": {}
        }
        
        try:
            # Basecamp status with project names
            if basecamp_service.enabled:
                for project_id in basecamp_service.project_ids:
                    last_sync = await basecamp_service.get_last_sync_time(project_id)
                    
                    # Get project name from Basecamp API if possible
                    project_name = project_id  # fallback
                    try:
                        async with httpx.AsyncClient() as client:
                            project_url = f"{basecamp_service.base_url}/{basecamp_service.account_id}/projects/{project_id}.json"
                            project_data = await basecamp_service._get(client, project_url)
                            if project_data and project_data.get("name"):
                                project_name = project_data["name"]
                    except Exception as e:
                        self.logger.debug(f"Could not fetch project name for {project_id}: {e}")
                    
                    status["basecamp"][project_id] = {
                        "project_name": project_name,
                        "last_sync": last_sync.isoformat() if last_sync else None,
                        "needs_sync": not last_sync or last_sync < (datetime.now(timezone.utc) - timedelta(hours=24))
                    }
            
            # Watchdog sources status
            from app.core.database import get_database
            db = await get_database()
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            sources_to_check = [
                "gmail_sync_state",
                "drive_sync_state", 
                "local_files_sync_state"
            ]
            
            for source_collection in sources_to_check:
                try:
                    last_sync_record = await db[source_collection].find_one(
                        sort=[("last_sync", -1)]
                    )
                    
                    if last_sync_record and last_sync_record.get("last_sync"):
                        last_sync = datetime.fromisoformat(
                            last_sync_record["last_sync"].replace("Z", "+00:00")
                        )
                        status["watchdog_sources"][source_collection] = {
                            "last_sync": last_sync.isoformat(),
                            "needs_sync": last_sync < cutoff_time
                        }
                    else:
                        status["watchdog_sources"][source_collection] = {
                            "last_sync": None,
                            "needs_sync": True
                        }
                        
                except Exception as e:
                    status["watchdog_sources"][source_collection] = {
                        "error": str(e),
                        "needs_sync": True
                    }
            
            # Add embedding status
            status["embedding_status"] = await self._get_embedding_status()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            status["error"] = str(e)
            return status
    
    async def _get_embedding_status(self) -> Dict[str, any]:
        """Get embedding status from Pinecone and processing queue."""
        embedding_status = {
            "pinecone_status": {"status": "checking"},
            "queue_status": {},
            "total_embeddings": 0,
            "last_embedding_update": None
        }
        
        try:
            # Get Pinecone status
            from app.services.ingestion.pinecone_store import pinecone_store
            
            try:
                # Initialize Pinecone if not already done
                if not pinecone_store._initialized:
                    pinecone_store._initialize()
                
                if pinecone_store.index:
                    embedding_status["pinecone_status"] = {
                        "index_name": pinecone_store.index_name,
                        "status": "active",
                        "message": "Pinecone index is available"
                    }
                else:
                    embedding_status["pinecone_status"] = {
                        "status": "not_initialized",
                        "error": "Pinecone index not available"
                    }
                        
            except Exception as e:
                embedding_status["pinecone_status"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            # Get message queue status
            try:
                from app.core.memory_adapters import msg_queue
                queue_size = msg_queue.qsize()
                embedding_status["queue_status"] = {
                    "pending_documents": queue_size,
                    "status": "active" if queue_size >= 0 else "error"
                }
            except Exception as e:
                embedding_status["queue_status"] = {
                    "pending_documents": 0,
                    "status": "error",
                    "error": str(e)
                }
            
            # Get last embedding update from database
            try:
                from app.core.database import get_database
                db = await get_database()
                
                # Look for embedding processing logs or metadata
                last_embedding_record = await db.embedding_logs.find_one(
                    sort=[("timestamp", -1)]
                )
                
                if last_embedding_record:
                    embedding_status["last_embedding_update"] = last_embedding_record.get("timestamp")
                
            except Exception as e:
                # If no embedding logs collection, that's okay
                embedding_status["last_embedding_update"] = None
            
            return embedding_status
            
        except Exception as e:
            self.logger.error(f"Error getting embedding status: {e}")
            embedding_status["error"] = str(e)
            return embedding_status


# Singleton instance
startup_automation = StartupAutomation()
