"""
Strategy Section API

Endpoints for managing strategy section data:
- Stakeholder map, goals, upsell opportunities, competitors, ecosystem
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
SECTION = "strategy"


# --- Models ---

class Stakeholder(BaseModel):
    name: str
    role: str
    influence: Optional[str] = "Medium"
    sentiment: Optional[str] = "Neutral"
    notes: Optional[str] = None


class Goal(BaseModel):
    goal: str
    timeline: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "planned"


class UpsellOpportunity(BaseModel):
    opportunity: str
    value: Optional[str] = None
    likelihood: Optional[str] = "Medium"
    champion: Optional[str] = None


class Competitor(BaseModel):
    name: str
    strength: Optional[str] = None
    weakness: Optional[str] = None
    notes: Optional[str] = None


class EcosystemPlatform(BaseModel):
    platform: str
    purpose: Optional[str] = None


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
async def get_strategy(client_id: str, project_id: str, current_user: User = Depends(get_current_user)) -> Any:
    """Get entire strategy section."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    return {"section": SECTION, "data": data}


@router.put("/{client_id}/{project_id}")
async def update_strategy(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire strategy section. Access protected."""
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


# --- Stakeholder Map ---

def extract_nested_value(data):
    """Extract value from nested structure or return as-is."""
    if isinstance(data, dict) and "value" in data:
        return data
    return {"value": data if isinstance(data, list) else []}

@router.get("/{client_id}/{project_id}/stakeholders")
async def get_stakeholders(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    stakeholder_data = data.get("stakeholder_map", {})
    return {"field": "stakeholder_map", "data": extract_nested_value(stakeholder_data)}


@router.put("/{client_id}/{project_id}/stakeholders")
async def update_stakeholders(client_id: str, project_id: str, payload: List[Stakeholder], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "stakeholder_map", [s.dict() for s in payload], current_user)


@router.post("/{client_id}/{project_id}/stakeholders")
async def add_stakeholder(client_id: str, project_id: str, stakeholder: Stakeholder, current_user: User = Depends(get_current_user)):
    db = await get_database()
    # Ensure project access before modifying
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.stakeholder_map.value": stakeholder.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "stakeholder": stakeholder.dict()}


# --- Goals Roadmap ---

@router.get("/{client_id}/{project_id}/goals")
async def get_goals(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    goals_data = data.get("goals_roadmap", {})
    return {"field": "goals_roadmap", "data": extract_nested_value(goals_data)}


@router.put("/{client_id}/{project_id}/goals")
async def update_goals(client_id: str, project_id: str, payload: List[Goal], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "goals_roadmap", [g.dict() for g in payload])


@router.post("/{client_id}/{project_id}/goals")
async def add_goal(client_id: str, project_id: str, goal: Goal, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.goals_roadmap.value": goal.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "goal": goal.dict()}


# --- Upsell Opportunities ---

@router.get("/{client_id}/{project_id}/upsells")
async def get_upsells(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    upsells_data = data.get("upsell_opportunities", {})
    return {"field": "upsell_opportunities", "data": extract_nested_value(upsells_data)}


@router.put("/{client_id}/{project_id}/upsells")
async def update_upsells(client_id: str, project_id: str, payload: List[UpsellOpportunity], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "upsell_opportunities", [u.dict() for u in payload])


@router.post("/{client_id}/{project_id}/upsells")
async def add_upsell(client_id: str, project_id: str, upsell: UpsellOpportunity, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.upsell_opportunities.value": upsell.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "upsell": upsell.dict()}


# --- Competitors ---

@router.get("/{client_id}/{project_id}/competitors")
async def get_competitors(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    competitors_data = data.get("competitors", {})
    return {"field": "competitors", "data": extract_nested_value(competitors_data)}


@router.put("/{client_id}/{project_id}/competitors")
async def update_competitors(client_id: str, project_id: str, payload: List[Competitor], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "competitors", [c.dict() for c in payload])


@router.post("/{client_id}/{project_id}/competitors")
async def add_competitor(client_id: str, project_id: str, competitor: Competitor, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.competitors.value": competitor.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "competitor": competitor.dict()}


# --- Ecosystem ---

@router.get("/{client_id}/{project_id}/ecosystem")
async def get_ecosystem(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    ecosystem_data = data.get("ecosystem", {})
    return {"field": "ecosystem", "data": extract_nested_value(ecosystem_data)}


@router.put("/{client_id}/{project_id}/ecosystem")
async def update_ecosystem(client_id: str, project_id: str, payload: List[EcosystemPlatform], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "ecosystem", [e.dict() for e in payload])
