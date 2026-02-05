from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, ingest, dashboard, sections, automation,
    clients, projects,
    universal_context, operations, technical, commercial, strategy, marketing, other,
    reports_enhanced, chat
)
from app.api.v1.endpoints.reports_enhanced import router as enhanced_reports_router

api_router = APIRouter()

# Core routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(sections.router, prefix="/sections", tags=["sections"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(reports_enhanced.router, prefix="/reports", tags=["reports"])

# Entity CRUD routes
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# Section-specific CRUD routes
api_router.include_router(universal_context.router, prefix="/universal-context", tags=["universal_context"])
api_router.include_router(operations.router, prefix="/operations", tags=["operations"])
api_router.include_router(technical.router, prefix="/technical", tags=["technical"])
api_router.include_router(commercial.router, prefix="/commercial", tags=["commercial"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["strategy"])
api_router.include_router(marketing.router, prefix="/marketing", tags=["marketing"])
api_router.include_router(other.router, prefix="/other", tags=["other"])

# Intelligence Routes
from app.api.v1.endpoints import upsell, risk, knowledge
api_router.include_router(upsell.router, prefix="/intelligence/upsell", tags=["intelligence_upsell"])
api_router.include_router(risk.router, prefix="/intelligence/risk", tags=["intelligence_risk"])
api_router.include_router(knowledge.router, prefix="/intelligence/knowledge", tags=["intelligence_knowledge"])

# Chat Routes
from app.api.v1.endpoints import chat
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
