from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.services.intelligence.upsell_assistant import generate_upsell_opportunities
from app.core.database import get_database

router = APIRouter()

@router.post("/{project_id}/generate")
async def generate_project_upsell(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Triggers AI to generate upsell opportunities based on project Strategy + News.
    """
    # 1. Check Access
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Simple access check (can be refined via RBAC)
    if not current_user.is_superuser:
         # TODO: Add specific permission check
         pass

    # 2. Generate
    opportunities = await generate_upsell_opportunities(project_id)
    
    return {
        "status": "success",
        "project_id": project_id,
        "count": len(opportunities),
        "data": opportunities
    }


@router.get("/{project_id}")
async def get_project_upsell(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get stored upsell opportunities.
    """
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    intelligence = project.get("intelligence", {})
    opportunities = intelligence.get("upsell_opportunities", [])
    
    # Bridge: If no manually generated opportunities, fallback to RAG extracted ones from strategy section
    if not opportunities:
        strategy_section = project.get("strategy", {})
        if isinstance(strategy_section, dict):
            # Resolve Datapoint structure if present
            raw_upsells = strategy_section.get("upsell_opportunities")
            if isinstance(raw_upsells, dict) and "value" in raw_upsells:
                opportunities = raw_upsells.get("value", [])
            elif isinstance(raw_upsells, list):
                opportunities = raw_upsells

    return {
        "project_id": project_id,
        "last_updated": intelligence.get("upsell_updated_at"),
        "data": opportunities
    }
