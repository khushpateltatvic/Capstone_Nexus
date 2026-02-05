from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.ingestion.watchdog import watchdog
from app.services.ingestion.basecamp import basecamp_service
from app.core.memory_adapters import msg_queue
import logging

scheduler = AsyncIOScheduler()
logger = logging.getLogger("project_nexus")


async def daily_sync_job():
    """Daily sync job - runs every 24 hours."""
    logger.info("⏰ === DAILY SYNC JOB STARTED ===")
    try:
        # 1. Trigger watchdog sync (local files, Gmail, Drive)
        logger.info("🔄 Starting watchdog sync...")
        await watchdog.trigger_sync()
        logger.info("✅ Watchdog sync completed")
        
        # 2. Trigger Basecamp sync
        if basecamp_service.enabled:
            logger.info("🏕️ Starting Basecamp sync...")
            results = await basecamp_service.sync_all_projects()
            
            # Queue Basecamp documents for RAG processing - use project_name
            docs_queued = 0
            extraction_results = []
            
            for doc in results.get("documents", []):
                try:
                    project_name = doc.get("project_name", doc["project_id"])
                    safe_name = project_name.lower().replace(" ", "_").replace("-", "_")
                    
                    await msg_queue.enqueue({
                        "filename": f"{safe_name}.txt",
                        "content": doc["content"],
                        "client_id": safe_name,
                        "project_id": doc["project_id"],
                        "source": "basecamp",
                        "document_id": f"basecamp_{doc['project_id']}"
                    })
                    docs_queued += 1
                except Exception as e:
                    logger.error(f"❌ Failed to queue document for {doc.get('project_id', 'unknown')}: {e}")
            
            # TRIGGER COMPREHENSIVE EXTRACTION FOR ALL SOURCES
            logger.info("🧠 === TRIGGERING COMPREHENSIVE EXTRACTION ===")
            
            for doc in results.get("documents", []):
                project_id = doc["project_id"]
                project_name = doc.get("project_name", project_id)
                
                try:
                    logger.info(f"🔍 Extracting from ALL sources for: {project_name}")
                    
                    # Use RAG service for comprehensive extraction
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
                                "filename": f"daily_extraction_{project_id}",
                                "extraction_type": "comprehensive_multi_source",
                                "triggered_by": "daily_scheduler"
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
                        
                        logger.info(f"✅ Comprehensive extraction completed for {project_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Extraction failed for {project_name}: {e}")
                    extraction_results.append({
                        "project_id": project_id,
                        "project_name": project_name,
                        "status": "error",
                        "error": str(e)
                    })
            
            successful_extractions = len([r for r in extraction_results if r["status"] == "success"])
            logger.info(f"✅ Basecamp sync: {len(results.get('successful', []))} projects synced, {docs_queued} documents queued")
            logger.info(f"🧠 Comprehensive extraction: {successful_extractions} projects processed")
        else:
            logger.info("⏭️ Basecamp sync skipped (disabled)")
        
        logger.info("✅ === DAILY SYNC JOB COMPLETED ===")
    except Exception as e:
        logger.error(f"❌ Daily Sync Job Failed: {e}")
        import traceback
        logger.error(f"❌ Daily sync traceback: {traceback.format_exc()}")


async def basecamp_sync_job():
    """Dedicated Basecamp sync job."""
    logger.info("🏕️ === BASECAMP SYNC JOB STARTED ===")
    try:
        if not basecamp_service.enabled:
            logger.warning("⚠️ Basecamp not configured, skipping sync")
            return
            
        results = await basecamp_service.sync_all_projects()
        
        # Queue documents for RAG processing
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
            except Exception as e:
                logger.error(f"❌ Failed to queue document for {doc.get('project_id', 'unknown')}: {e}")
        
        logger.info(f"✅ === BASECAMP SYNC JOB COMPLETED ===")
        logger.info(f"📊 Results: {len(results.get('successful', []))} successful, {docs_queued} documents queued")
    except Exception as e:
        logger.error(f"❌ Basecamp Sync Failed: {e}")
        import traceback
        logger.error(f"❌ Basecamp sync traceback: {traceback.format_exc()}")


def start_scheduler():
    """Start the automation scheduler."""
    try:
        logger.info("📅 === STARTING AUTOMATION SCHEDULER ===")
        
        # Daily sync job (24 hours) - includes all sources
        scheduler.add_job(
            daily_sync_job,
            trigger=IntervalTrigger(hours=24),
            id="daily_sync",
            replace_existing=True
        )
        logger.info("✅ Daily sync job scheduled (every 24 hours)")

        # Weekly Executive Briefing (Monday 9 AM UTC)
        from apscheduler.triggers.cron import CronTrigger
        from app.services.reporting.briefing import generate_executive_briefing
        
        scheduler.add_job(
            generate_executive_briefing,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id="weekly_briefing",
            replace_existing=True
        )
        logger.info("✅ Weekly briefing job scheduled (Mondays 9 AM UTC)")
        
        scheduler.start()
        logger.info("🎉 === AUTOMATION SCHEDULER STARTED SUCCESSFULLY ===")
        
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        import traceback
        logger.error(f"❌ Scheduler traceback: {traceback.format_exc()}")
        raise
