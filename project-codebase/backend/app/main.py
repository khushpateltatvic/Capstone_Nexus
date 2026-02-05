from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import db
from app.api.v1.api import api_router
from app.services.ingestion.watchdog import watchdog
from app.services.ingestion.processor import processor
from app.services.automation.startup_automation import startup_automation
from app.core.scheduler import start_scheduler
import asyncio
import logging

setup_logging()
logger = logging.getLogger("project_nexus")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME, "version": "1.0.0"}

async def safe_startup_task(name: str, coroutine):
    try:
        logger.info(f"🚀 Starting {name}...")
        await coroutine
        logger.info(f"✅ {name} started successfully")
    except Exception as e:
        logger.error(f"❌ {name} failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 === PROJECT NEXUS STARTUP ===")
    
    try:
        # Initialize database first
        logger.info("📊 Connecting to database...")
        await db.connect()
        logger.info("✅ Database connected successfully")
        
        # Start background workers with proper error handling
        logger.info("🔧 Starting background services...")
        
        # Create tasks with error handling
        watchdog_task = asyncio.create_task(
            safe_startup_task("Watchdog Service", watchdog.start())
        )
        
        processor_task = asyncio.create_task(
            safe_startup_task("Processor Service", processor.start())
        )
        
        # Run startup automation immediately (not as background task)
        logger.info("🤖 Running startup automation check...")
        try:
            automation_results = await startup_automation.check_and_run_automation()
            logger.info(f"✅ Startup automation completed: {automation_results}")
        except Exception as e:
            logger.error(f"❌ Startup automation failed: {e}")
            import traceback
            logger.error(f"❌ Startup automation traceback: {traceback.format_exc()}")
        
        # Start the scheduler
        logger.info("📅 Starting automation scheduler...")
        try:
            start_scheduler()
            logger.info("✅ Automation scheduler started successfully")
        except Exception as e:
            logger.error(f"❌ Scheduler failed to start: {e}")
        
        logger.info("🎉 === PROJECT NEXUS STARTUP COMPLETE ===")
        
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        import traceback
        logger.error(f"❌ Startup traceback: {traceback.format_exc()}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    await db.close()
