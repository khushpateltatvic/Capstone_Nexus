"""
Technical Section API

Endpoints for managing technical section data:
- Tech stack, access credentials, implementation log, experiments
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
SECTION = "technical"


# --- Models ---

class TechStackItem(BaseModel):
    technology: str
    category: Optional[str] = None  # frontend, backend, database, etc.
    version: Optional[str] = None
    notes: Optional[str] = None


class TechStackGrouped(BaseModel):
    active: Optional[List[str]] = []
    planned: Optional[List[str]] = []
    deprecated: Optional[List[str]] = []


class AccessCredential(BaseModel):
    service: str
    url: Optional[str] = None
    access_method: Optional[str] = None


class ImplementationLog(BaseModel):
    date: str
    task: str
    owner: Optional[str] = None


class Experiment(BaseModel):
    name: str
    hypothesis: Optional[str] = None
    result: Optional[str] = None
    improvement: Optional[str] = None
    deployed_date: Optional[str] = None


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
async def get_technical(client_id: str, project_id: str, current_user: User = Depends(get_current_user)) -> Any:
    """Get entire technical section."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    return {"section": SECTION, "data": data}


@router.put("/{client_id}/{project_id}")
async def update_technical(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire technical section. Access protected."""
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


# --- Tech Stack ---

def extract_nested_value(data):
    """Extract value from nested structure or return as-is."""
    if isinstance(data, dict) and "value" in data:
        return data
    return {"value": data if data else []}

@router.get("/{client_id}/{project_id}/tech_stack")
async def get_tech_stack(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    tech_stack_data = data.get("tech_stack", {})
    return {"field": "tech_stack", "data": extract_nested_value(tech_stack_data)}


@router.put("/{client_id}/{project_id}/tech_stack")
async def update_tech_stack(client_id: str, project_id: str, payload: TechStackGrouped, current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "tech_stack", payload.dict(), current_user)


@router.post("/{client_id}/{project_id}/tech_stack")
async def add_tech(client_id: str, project_id: str, tech: TechStackItem, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.tech_stack.value": tech.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "tech": tech.dict()}


# --- Access Credentials ---

@router.get("/{client_id}/{project_id}/credentials")
async def get_credentials(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    creds_data = data.get("access_credentials", {})
    return {"field": "access_credentials", "data": extract_nested_value(creds_data)}


@router.put("/{client_id}/{project_id}/credentials")
async def update_credentials(client_id: str, project_id: str, payload: List[AccessCredential], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "access_credentials", {"value": [c.dict() for c in payload]}, current_user)


@router.post("/{client_id}/{project_id}/credentials")
async def add_credential(client_id: str, project_id: str, cred: AccessCredential, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.access_credentials.value": cred.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "credential": cred.dict()}


# --- Implementation Log ---

@router.get("/{client_id}/{project_id}/implementations")
async def get_implementations(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    impl_data = data.get("implementation_log", {})
    return {"field": "implementation_log", "data": extract_nested_value(impl_data)}


@router.put("/{client_id}/{project_id}/implementations")
async def update_implementations(client_id: str, project_id: str, payload: List[ImplementationLog], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "implementation_log", {"value": [i.dict() for i in payload]}, current_user)


@router.post("/{client_id}/{project_id}/implementations")
async def add_implementation(client_id: str, project_id: str, impl: ImplementationLog, current_user: User = Depends(get_current_user)):
    db = await get_database()
    # Ensure project access before modifying
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.implementation_log.value": impl.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "implementation": impl.dict()}


# --- Experiments ---

@router.get("/{client_id}/{project_id}/experiments")
async def get_experiments(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    exp_data = data.get("experiment_results", data.get("experiments", {}))
    return {"field": "experiment_results", "data": extract_nested_value(exp_data)}


@router.put("/{client_id}/{project_id}/experiments")
async def update_experiments(client_id: str, project_id: str, payload: List[Experiment], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "experiment_results", {"value": [e.dict() for e in payload]}, current_user)


@router.post("/{client_id}/{project_id}/experiments")
async def add_experiment(client_id: str, project_id: str, exp: Experiment, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.experiment_results.value": exp.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "experiment": exp.dict()}
