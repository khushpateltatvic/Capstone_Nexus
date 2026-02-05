"""
Marketing Section API
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
SECTION = "marketing"


class BrandGuidelines(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    typography: Optional[str] = None
    tone: Optional[str] = None


class SuccessStory(BaseModel):
    title: str
    description: Optional[str] = None


class Testimonial(BaseModel):
    from_person: str
    quote: str


class PublicReference(BaseModel):
    type: str
    title: str
    url: Optional[str] = None


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
async def get_marketing(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    return {"section": SECTION, "data": await get_section(db, client_id, project_id, current_user)}


@router.put("/{client_id}/{project_id}")
async def update_marketing(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire marketing section. Access protected."""
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
    return {"value": data if data else []}


@router.get("/{client_id}/{project_id}/brand")
async def get_brand(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    brand_data = data.get("brand_guidelines", {})
    return {"field": "brand_guidelines", "data": extract_nested_value(brand_data)}


@router.put("/{client_id}/{project_id}/brand")
async def update_brand(client_id: str, project_id: str, payload: BrandGuidelines, current_user: User = Depends(get_current_user)):
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    return await update_field(db, client_id, project_id, "brand_guidelines", payload.dict(), current_user)


@router.get("/{client_id}/{project_id}/success_stories")
async def get_stories(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    stories_data = data.get("success_stories", {})
    return {"field": "success_stories", "data": extract_nested_value(stories_data)}


@router.put("/{client_id}/{project_id}/success_stories")
async def update_stories(client_id: str, project_id: str, payload: List[SuccessStory], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "success_stories", [s.dict() for s in payload], current_user)


@router.get("/{client_id}/{project_id}/testimonials")
async def get_testimonials(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    testimonials_data = data.get("testimonials", {})
    return {"field": "testimonials", "data": extract_nested_value(testimonials_data)}


@router.put("/{client_id}/{project_id}/testimonials")
async def update_testimonials(client_id: str, project_id: str, payload: List[Testimonial], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "testimonials", [t.dict() for t in payload], current_user)


@router.get("/{client_id}/{project_id}/references")
async def get_refs(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_section(db, client_id, project_id, current_user)
    refs_data = data.get("public_references", {})
    return {"field": "public_references", "data": extract_nested_value(refs_data)}


@router.put("/{client_id}/{project_id}/references")
async def update_refs(client_id: str, project_id: str, payload: List[PublicReference], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "public_references", [r.dict() for r in payload], current_user)


@router.post("/{client_id}/{project_id}/generate")
async def generate_marketing(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    """
    Trigger automated generation of marketing intelligence using Gemini.
    Extracts data from Universal Context & Strategy to populate Marketing fields.
    """
    from app.services.marketing_extraction import generate_marketing_intelligence
    
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check permissions (Managers+)
    if not has_project_access(current_user, project):
         raise HTTPException(status_code=403, detail="You don't have access to this project")
         
    # Fetch Client for name
    client = await db.clients.find_one({"client_id": client_id})
    client_name = client.get("name") if client else "Unknown Client"
         
    try:
        data = await generate_marketing_intelligence(project_id, client_id, client_name)
        if not data:
            return {"status": "skipped", "message": "No context available to generate data"}
            
        return {"status": "success", "message": "Marketing intelligence generated", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
