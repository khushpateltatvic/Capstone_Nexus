"""
Universal Context Section API

Endpoints for managing universal_context section data:
- Account summary, timeline, engagement type, client profile
- Internal squad, POC map, communication hygiene
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
SECTION = "universal_context"


# --- Models ---

class TimelineEvent(BaseModel):
    date: str
    event: str
    significance: Optional[str] = "Medium"


class POCContact(BaseModel):
    name: str
    role: str
    email: Optional[str] = None
    influence: Optional[str] = "Medium"
    sentiment: Optional[str] = "Neutral"


class SquadMember(BaseModel):
    name: str
    role: str
    email: Optional[str] = None


class CommunicationHygiene(BaseModel):
    last_email: Optional[str] = None
    last_meeting: Optional[str] = None
    response_time: Optional[str] = None
    meeting_frequency: Optional[str] = None


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


@router.get("/squad-search-users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    """Get all users for squad member search"""
    db = await get_database()
    users = await db.users.find({}).to_list(length=None)
    return {
        "users": [
            {
                "email": u.get("email"),
                "name": u.get("full_name", u.get("email")),
                "role": u.get("role", "analyst"),
                "department": u.get("department", "")
            }
            for u in users
        ]
    }


# --- Endpoints ---

@router.get("/{client_id}/{project_id}")
async def get_universal_context(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get entire universal_context section."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    return {"section": SECTION, "data": data}


@router.put("/{client_id}/{project_id}")
async def update_universal_context(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire universal_context section."""
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


def extract_nested_value(data):
    """Extract value from nested structure or return as-is."""
    if isinstance(data, dict) and "value" in data:
        return data
    return {"value": data} if data else {}


# --- Summary ---

@router.get("/{client_id}/{project_id}/summary")
async def get_summary(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    summary_data = data.get("summary", {})
    return {"field": "summary", "data": extract_nested_value(summary_data)}


@router.put("/{client_id}/{project_id}/summary")
async def update_summary(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "summary", payload.get("value", payload))


# --- Timeline ---

@router.get("/{client_id}/{project_id}/timeline")
async def get_timeline(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    timeline_data = data.get("timeline", {})
    if isinstance(timeline_data, dict) and "value" in timeline_data:
        return {"field": "timeline", "data": timeline_data}
    return {"field": "timeline", "data": {"value": timeline_data if isinstance(timeline_data, list) else []}}


@router.put("/{client_id}/{project_id}/timeline")
async def update_timeline(client_id: str, project_id: str, payload: List[TimelineEvent], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "timeline", [e.dict() for e in payload])


@router.post("/{client_id}/{project_id}/timeline")
async def add_timeline_event(client_id: str, project_id: str, event: TimelineEvent, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.timeline.value": event.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "event": event.dict()}


# --- POC Map ---

@router.get("/{client_id}/{project_id}/poc_map")
async def get_poc_map(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    poc_data = data.get("poc_map", {})
    if isinstance(poc_data, dict) and "value" in poc_data:
        return {"field": "poc_map", "data": poc_data}
    return {"field": "poc_map", "data": {"value": poc_data if isinstance(poc_data, list) else []}}


@router.put("/{client_id}/{project_id}/poc_map")
async def update_poc_map(client_id: str, project_id: str, payload: List[POCContact], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "poc_map", [p.dict() for p in payload])


@router.post("/{client_id}/{project_id}/poc_map")
async def add_poc(client_id: str, project_id: str, poc: POCContact, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.poc_map.value": poc.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "poc": poc.dict()}


# --- Internal Squad ---

@router.get("/{client_id}/{project_id}/internal_squad")
async def get_squad(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    squad_data = data.get("squad", {})
    if isinstance(squad_data, dict) and "value" in squad_data:
        return {"field": "internal_squad", "data": squad_data}
    return {"field": "internal_squad", "data": {"value": squad_data if isinstance(squad_data, list) else []}}


@router.put("/{client_id}/{project_id}/internal_squad")
async def update_squad(client_id: str, project_id: str, payload: List[SquadMember], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "squad", [s.dict() for s in payload], current_user)


@router.post("/{client_id}/{project_id}/internal_squad")
async def add_squad_member(client_id: str, project_id: str, member: SquadMember, current_user: User = Depends(get_current_user)):
    """Add a squad member and grant them project access"""
    db = await get_database()
    
    # Verify project access
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Add member to squad
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$push": {f"{SECTION}.squad.value": member.dict()},
            "$addToSet": {"access.assigned_users": member.email},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return {"status": "added", "member": member.dict(), "access_granted": True}


# --- Communication Hygiene ---

@router.get("/{client_id}/{project_id}/communication")
async def get_communication(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    comm_data = data.get("communication_hygiene", {})
    return {"field": "communication_hygiene", "data": extract_nested_value(comm_data)}


@router.put("/{client_id}/{project_id}/communication")
async def update_communication(client_id: str, project_id: str, payload: CommunicationHygiene, current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "communication_hygiene", payload.dict())


# --- Client Profile ---

@router.get("/{client_id}/{project_id}/client_profile")
async def get_client_profile(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    """Get client profile data including health score and company info."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    profile_data = data.get("client_profile", {})
    return {"field": "client_profile", "data": extract_nested_value(profile_data)}


@router.put("/{client_id}/{project_id}/client_profile")
async def update_client_profile(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "client_profile", payload.get("value", payload))


# --- Engagement Type ---

@router.get("/{client_id}/{project_id}/engagement_type")
async def get_engagement(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    engagement_data = data.get("engagement_type", {})
    return {"field": "engagement_type", "data": extract_nested_value(engagement_data)}


@router.put("/{client_id}/{project_id}/engagement_type")
async def update_engagement(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "engagement_type", payload.get("value", payload))


# --- Important Notes ---

@router.get("/{client_id}/{project_id}/important_notes")
async def get_important_notes(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    notes_data = data.get("important_notes", {})
    if isinstance(notes_data, dict) and "value" in notes_data:
        return {"field": "important_notes", "data": notes_data}
    return {"field": "important_notes", "data": {"value": notes_data if isinstance(notes_data, list) else []}}


@router.put("/{client_id}/{project_id}/important_notes")
async def update_important_notes(client_id: str, project_id: str, payload: List[str], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "important_notes", payload)


@router.post("/{client_id}/{project_id}/important_notes")
async def add_important_note(client_id: str, project_id: str, payload: Dict[str, str], current_user: User = Depends(get_current_user)):
    db = await get_database()
    note = payload.get("note", "")
    if note:
        await db.projects.update_one(
            {"client_id": client_id, "project_id": project_id},
            {"$push": {f"{SECTION}.important_notes.value": note}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
        )
    return {"status": "added", "note": note}


# --- Google Workspace ---

@router.get("/{client_id}/{project_id}/google_workspace")
async def get_google_workspace(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    ws_data = data.get("google_workspace", {})
    if isinstance(ws_data, dict) and "value" in ws_data:
        return {"field": "google_workspace", "data": ws_data}
    return {"field": "google_workspace", "data": {"value": ws_data if isinstance(ws_data, list) else []}}


@router.put("/{client_id}/{project_id}/google_workspace")
async def update_google_workspace(client_id: str, project_id: str, payload: List[str], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "google_workspace", payload)
