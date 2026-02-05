from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from app.models.domain.user import User
from app.models.domain.core_entities import Project
from app.models.domain.access_control import RolePermission
from app.models.domain.document_references import InternalStakeholder, ProjectAssignment
from app.services.context_manager import context_manager

router = APIRouter()

# --- Schemas ---

class UserListResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str

class AssignmentRequest(BaseModel):
    email: str
    role_in_project: str
    view_access: List[str] = [] # List of section keys to ALLOW VIEW
    edit_access: List[str] = [] # List of section keys to ALLOW EDIT

class AssignmentResponse(BaseModel):
    project_id: str
    user_name: str
    role_in_project: str
    view_count: int
    edit_count: int

# --- Endpoints ---

@router.get("/users", response_model=List[UserListResponse])
async def list_users():
    """List all users available for assignment (Manually resolving links to avoid Motor TypeError)"""
    users = await User.find_all().to_list()
    response = []
    for u in users:
        dept = "Unknown"
        # Manual link resolution instead of fetch_links=True to avoid AsyncIOMotorLatentCommandCursor error
        if u.internal_stakeholder:
             stakeholder = await u.internal_stakeholder.fetch()
             if stakeholder:
                 dept = stakeholder.department or "Unknown"
             
        response.append(UserListResponse(
            id=str(u.id),
            name=u.full_name or "Unknown",
            email=u.email,
            role=u.role,
            department=dept
        ))
    return response

@router.get("/roles")
async def list_active_roles():
    """List all active role profiles in the organization"""
    roles = await RolePermission.find_all().to_list()
    return [
        {
            "role": r.role,
            "department": r.department,
            "permissions_count": len(r.permissions)
        }
        for r in roles
    ]

@router.get("/projects/{project_id}/team", response_model=List[AssignmentResponse])
async def get_project_team(project_id: str):
    """Get current team assignments for a project"""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    assignments = await ProjectAssignment.find(ProjectAssignment.project.id == project.id).to_list()
    response = []
    for a in assignments:
        u_name = "Unknown"
        stakeholder = await a.internal_stakeholder.fetch()
        if stakeholder:
            u_name = stakeholder.name
            
        response.append(AssignmentResponse(
            project_id=str(project.id),
            user_name=u_name,
            role_in_project=a.role_in_project,
            view_count=len(a.custom_view_access),
            edit_count=len(a.custom_edit_access)
        ))
    return response

@router.post("/projects/{project_id}/assign", response_model=AssignmentResponse)
async def assign_user_to_project(project_id: str, payload: AssignmentRequest):
    """
    Assign a user to a project with specific Custom Access overrides.
    """
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == payload.email)
    if not stakeholder:
        raise HTTPException(status_code=404, detail=f"Internal User with email {payload.email} not found")

    assignment = await ProjectAssignment.find_one(
        ProjectAssignment.project.id == project.id,
        ProjectAssignment.internal_stakeholder.id == stakeholder.id
    )
    
    if assignment:
        assignment.role_in_project = payload.role_in_project
        assignment.custom_view_access = payload.view_access
        assignment.custom_edit_access = payload.edit_access
        await assignment.save()
    else:
        assignment = ProjectAssignment(
            project=project,
            internal_stakeholder=stakeholder,
            role_in_project=payload.role_in_project,
            custom_view_access=payload.view_access,
            custom_edit_access=payload.edit_access
        )
        await assignment.insert()

    return AssignmentResponse(
        project_id=str(project.id),
        user_name=stakeholder.name,
        role_in_project=assignment.role_in_project,
        view_count=len(assignment.custom_view_access),
        edit_count=len(assignment.custom_edit_access)
    )
