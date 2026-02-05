"""
Other Section API - Miscellaneous data
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access

router = APIRouter()
SECTION = "other"


class Note(BaseModel):
    title: str
    content: str
    created_at: Optional[str] = None


async def get_section(db, client_id: str, project_id: str, user: User):
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    return project.get(SECTION, {})


async def update_field(db, client_id: str, project_id: str, field: str, value: Any, user: User):
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
        
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": {f"{SECTION}.{field}": value, "updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "updated", "field": field}


@router.get("/{client_id}/{project_id}")
async def get_other(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    return {"section": SECTION, "data": await get_section(db, client_id, project_id, current_user)}


@router.put("/{client_id}/{project_id}")
async def update_other(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire other section. Access protected."""
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": {SECTION: payload, "updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "updated", "section": SECTION}


@router.get("/{client_id}/{project_id}/notes")
async def get_notes(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    return {"field": "notes", "data": data.get("notes", [])}


@router.put("/{client_id}/{project_id}/notes")
async def update_notes(client_id: str, project_id: str, payload: List[Note], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "notes", [n.dict() for n in payload])


@router.post("/{client_id}/{project_id}/notes")
async def add_note(client_id: str, project_id: str, note: Note, current_user: User = Depends(get_current_user)):
    # Access Check
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
        
    note_dict = note.dict()
    note_dict["created_at"] = datetime.utcnow().isoformat()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.notes.value": note_dict}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "note": note_dict}


@router.get("/{client_id}/{project_id}/custom/{field_name}")
async def get_custom(client_id: str, project_id: str, field_name: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    return {"field": field_name, "data": data.get(field_name)}


@router.put("/{client_id}/{project_id}/custom/{field_name}")
async def update_custom(client_id: str, project_id: str, field_name: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, field_name, payload, current_user)
