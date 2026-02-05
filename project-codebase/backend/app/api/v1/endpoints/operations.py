"""
Operations Section API

Endpoints for managing operations section data:
- Traffic light status, task board, blockers, recent interactions
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
SECTION = "operations"


# --- Models ---

class Task(BaseModel):
    title: str
    status: Optional[str] = "pending"
    due_date: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = "Medium"


class Blocker(BaseModel):
    description: str
    severity: Optional[str] = "Medium"
    owner: Optional[str] = None
    created_at: Optional[str] = None


class Interaction(BaseModel):
    date: str
    type: str  # meeting, email, call
    summary: str
    attendees: Optional[List[str]] = []


# --- Helper ---

async def get_project_section(db, client_id: str, project_id: str, user: User):
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


# --- Endpoints ---

@router.get("/{client_id}/{project_id}")
async def get_operations(client_id: str, project_id: str, current_user: User = Depends(get_current_user)) -> Any:
    """Get entire operations section."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    return {"section": SECTION, "data": data}


@router.put("/{client_id}/{project_id}")
async def update_operations(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire operations section. Access protected."""
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


# --- Traffic Light ---

@router.get("/{client_id}/{project_id}/traffic_light")
async def get_traffic_light(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    traffic_light = data.get("traffic_light", {})
    # Handle nested value structure from RAG extraction
    if isinstance(traffic_light, dict) and "value" in traffic_light:
        return {"field": "traffic_light", "data": {"value": traffic_light.get("value"), "reason": traffic_light.get("reason", traffic_light.get("source_doc", ""))}}
    return {"field": "traffic_light", "data": traffic_light}


@router.put("/{client_id}/{project_id}/traffic_light")
async def update_traffic_light(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update traffic light. Payload: {"value": "Green/Yellow/Red", "reason": "..."}"""
    db = await get_database()
    return await update_field(db, client_id, project_id, "traffic_light", payload)


# --- Task Board ---

def extract_value(data):
    """Extract value from nested structure or return as-is."""
    if isinstance(data, dict) and "value" in data:
        return data.get("value", [])
    return data if data else []

@router.get("/{client_id}/{project_id}/tasks")
async def get_tasks(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    upcoming = extract_value(data.get("task_board_upcoming", []))
    ongoing = extract_value(data.get("task_board_ongoing", []))
    return {
        "upcoming": {"value": upcoming},
        "ongoing": {"value": ongoing}
    }


@router.put("/{client_id}/{project_id}/tasks/upcoming")
async def update_upcoming_tasks(client_id: str, project_id: str, payload: List[Task], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "task_board_upcoming", [t.dict() for t in payload])


@router.put("/{client_id}/{project_id}/tasks/ongoing")
async def update_ongoing_tasks(client_id: str, project_id: str, payload: List[Task], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "task_board_ongoing", [t.dict() for t in payload])


@router.post("/{client_id}/{project_id}/tasks/upcoming")
async def add_upcoming_task(client_id: str, project_id: str, task: Task, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.task_board_upcoming.value": task.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "task": task.dict()}


@router.post("/{client_id}/{project_id}/tasks/ongoing")
async def add_ongoing_task(client_id: str, project_id: str, task: Task, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.task_board_ongoing.value": task.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "task": task.dict()}


# --- Blockers ---

@router.get("/{client_id}/{project_id}/blockers")
async def get_blockers(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    blockers_data = data.get("blockers", {})
    # Handle nested value structure from RAG extraction
    if isinstance(blockers_data, dict) and "value" in blockers_data:
        return {"field": "blockers", "data": blockers_data}
    return {"field": "blockers", "data": {"value": blockers_data if isinstance(blockers_data, list) else []}}


@router.put("/{client_id}/{project_id}/blockers")
async def update_blockers(client_id: str, project_id: str, payload: List[Blocker], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "blockers", [b.dict() for b in payload], current_user)


@router.post("/{client_id}/{project_id}/blockers")
async def add_blocker(client_id: str, project_id: str, blocker: Blocker, current_user: User = Depends(get_current_user)):
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    blocker_dict = blocker.dict()
    blocker_dict["created_at"] = datetime.utcnow().isoformat()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.blockers.value": blocker_dict}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "blocker": blocker_dict}


# --- Recent Interactions ---

@router.get("/{client_id}/{project_id}/interactions")
async def get_interactions(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    interactions_data = data.get("recent_interactions", {})
    # Handle nested value structure from RAG extraction
    if isinstance(interactions_data, dict) and "value" in interactions_data:
        return {"field": "recent_interactions", "data": interactions_data}
    return {"field": "recent_interactions", "data": {"value": interactions_data if isinstance(interactions_data, list) else []}}


@router.put("/{client_id}/{project_id}/interactions")
async def update_interactions(client_id: str, project_id: str, payload: List[Interaction], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "recent_interactions", [i.dict() for i in payload])


@router.post("/{client_id}/{project_id}/interactions")
async def add_interaction(client_id: str, project_id: str, interaction: Interaction, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.recent_interactions.value": interaction.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "interaction": interaction.dict()}
