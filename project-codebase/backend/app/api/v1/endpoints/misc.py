from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.domain.sections import MiscState
from app.models.domain.core_entities import Project
from app.models.schemas.sections import MiscStateRead, MiscStateUpdate
from app.api.v1.endpoints.access_control import get_current_stakeholder
from app.models.domain.document_references import InternalStakeholder
from app.services.access_control import access_control
from datetime import datetime

router = APIRouter()

@router.get("/{project_id}", response_model=MiscStateRead)
async def get_misc_state(
    project_id: str,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Get the misc state for a project"""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not await access_control.can_user_view_section(current_user, project, "7_misc"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to view this section")
        
    doc = await MiscState.find_one(MiscState.project.id == project.id)
    if not doc:
        return MiscStateRead(
            id="new", project_id=project_id, 
            feedback=[], subscriptions=[], reference_docs=[], additional_emails=[],
            last_updated=datetime.utcnow()
        )
    return doc

@router.patch("/{project_id}", response_model=MiscStateRead)
async def update_misc_state(
    project_id: str,
    request: MiscStateUpdate,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Update the misc state for a project"""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not await access_control.can_user_edit_section(current_user, project, "7_misc"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit this section")
        
    doc = await MiscState.find_one(MiscState.project.id == project.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Section record not found")
        
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)
    
    doc.last_updated = datetime.utcnow()
    await doc.save()
    return doc

@router.delete("/{project_id}")
async def delete_misc_state(
    project_id: str,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Reset/Delete the misc state for a project"""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not await access_control.can_user_edit_section(current_user, project, "7_misc"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete this section")
        
    doc = await MiscState.find_one(MiscState.project.id == project.id)
    if doc:
        await doc.delete()
        
    return {"status": "success", "message": "Section data deleted"}
