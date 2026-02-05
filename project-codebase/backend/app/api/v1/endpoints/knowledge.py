from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.services.intelligence.knowledge_bridge import find_knowledge_proposals
from app.core.database import get_database

router = APIRouter()

@router.get("/{project_id}/matches")
async def get_knowledge_matches(
    project_id: str,
    refresh: bool = False,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get matching success stories from other projects.
    """
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    intelligence = project.get("intelligence", {})
    existing = intelligence.get("knowledge_matches")
    
    if refresh or not existing:
        matches = await find_knowledge_proposals(project_id)
        return {"status": "success", "source": "generated", "data": matches}
        
    return {"status": "success", "source": "cached", "data": existing}
