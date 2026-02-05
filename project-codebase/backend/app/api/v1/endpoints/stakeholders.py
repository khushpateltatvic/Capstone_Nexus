from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.domain.document_references import ExternalStakeholder, InternalStakeholder
from app.models.domain.core_entities import Project
from app.models.schemas.stakeholders import ExternalStakeholderRead, ExternalStakeholderUpdate
from app.api.v1.endpoints.access_control import get_current_stakeholder
from app.services.access_control import access_control
from datetime import datetime

router = APIRouter()

@router.get("/{project_id}", response_model=List[ExternalStakeholderRead])
async def list_project_stakeholders(
    project_id: str,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """List all external stakeholders (POCs, etc.) for a project"""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
    # Validation: Need access to project
    if not await access_control.can_user_access_project(current_user, project):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this project")
        
    stakeholders = await ExternalStakeholder.find(
        ExternalStakeholder.project.id == project.id
    ).to_list()
    
    return [
        ExternalStakeholderRead(
            id=str(s.id),
            project_id=str(s.project.ref.id),
            name=s.name,
            role=s.role,
            category=s.category,
            email=s.email,
            phone=s.phone,
            sentiment=s.sentiment,
            influence=s.influence,
            last_updated=s.last_updated
        ) for s in stakeholders
    ]

@router.patch("/{stakeholder_id}", response_model=ExternalStakeholderRead)
async def update_stakeholder(
    stakeholder_id: str,
    request: ExternalStakeholderUpdate,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Manually update an external stakeholder's details"""
    sh = await ExternalStakeholder.get(stakeholder_id)
    if not sh:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
        
    project = await sh.project.fetch()
    # Check edit permission for Universal Context (as proxy for POCs)
    if not await access_control.can_user_edit_section(current_user, project, "1_universal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to edit stakeholders")
        
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sh, field, value)
        
    sh.last_updated = datetime.utcnow()
    await sh.save()
    
    return ExternalStakeholderRead(
        id=str(sh.id),
        project_id=str(sh.project.ref.id),
        name=sh.name,
        role=sh.role,
        category=sh.category,
        email=sh.email,
        phone=sh.phone,
        sentiment=sh.sentiment,
        influence=sh.influence,
        last_updated=sh.last_updated
    )

@router.delete("/{stakeholder_id}")
async def delete_stakeholder(
    stakeholder_id: str,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Remove a stakeholder record"""
    sh = await ExternalStakeholder.get(stakeholder_id)
    if not sh:
        raise HTTPException(status_code=404, detail="Stakeholder not found")
        
    project = await sh.project.fetch()
    if not await access_control.can_user_edit_section(current_user, project, "1_universal"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to delete stakeholders")
        
    await sh.delete()
    return {"status": "success", "message": "Stakeholder removed"}
