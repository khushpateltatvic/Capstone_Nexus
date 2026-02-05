"""
Access Control Management API
Handles user permissions, role assignments, and access control
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime

from app.models.domain.document_references import (
    InternalStakeholder, ClientStakeholder, AccessControlRule, AccessLevel, ProjectAssignment
)
from app.models.domain.core_entities import Client, Project
from app.services.access_control import access_control
from app.services.context_manager import context_manager
from app.models.domain.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.core.logging_config import logger

router = APIRouter()

async def get_current_stakeholder(current_user: User = Depends(get_current_user)) -> InternalStakeholder:
    """
    Dependency to get the InternalStakeholder associated with the current User.
    If no stakeholder exists and the user is an Executive, it bootstraps the profile.
    """
    stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == current_user.email)
    
    if not stakeholder:
        # Bootstrap: If user is Executive, auto-create the internal stakeholder profile
        if current_user.role == "Executive":
            stakeholder = InternalStakeholder(
                name=current_user.full_name or "Initial Executive",
                email=current_user.email,
                role="Executive",
                seniority_level="executive",
                department="Management",
                access_level=AccessLevel(level="executive", data_access_level="executive")
            )
            await stakeholder.insert()
            logger.info(f"Bootstrapped InternalStakeholder for executive: {current_user.email}")
            return stakeholder
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have an associated internal stakeholder profile"
        )
    return stakeholder

# Request/Response Models
class CreateInternalStakeholderRequest(BaseModel):
    name: str
    email: str
    role: str
    department: Optional[str] = None
    seniority_level: str = "junior"
    reports_to_email: Optional[str] = None

class UpdateStakeholderAccessRequest(BaseModel):
    stakeholder_email: str
    seniority_level: Optional[str] = None
    permissions: Optional[List[str]] = None
    can_view_clients: Optional[List[str]] = None
    can_view_projects: Optional[List[str]] = None
    data_access_level: Optional[str] = None

class ProjectAssignmentRequest(BaseModel):
    stakeholder_email: str
    project_id: str
    role_in_project: str
    allocation_percentage: Optional[float] = None
    can_view_sensitive_data: bool = False
    can_modify_project: bool = False
    can_add_team_members: bool = False

class AccessControlRuleRequest(BaseModel):
    rule_name: str
    rule_type: str
    applies_to_roles: Optional[List[str]] = None
    applies_to_seniority: Optional[List[str]] = None
    applies_to_departments: Optional[List[str]] = None
    permissions: List[str]
    data_access_levels: Optional[List[str]] = None
    restricted_clients: Optional[List[str]] = None
    restricted_projects: Optional[List[str]] = None

@router.post("/stakeholders/internal")
async def create_internal_stakeholder(
    request: CreateInternalStakeholderRequest,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Create a new internal stakeholder (requires manager+ level)"""
    
    # Check if current user can add team members
    permissions = await access_control.get_user_permissions(current_user)
    if "add_team_members" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to add team members"
        )
    
    # Check if current user can assign this seniority level
    if not await access_control.can_user_assign_role(current_user, None, request.seniority_level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign seniority level '{request.seniority_level}'"
        )
    
    # Find reports_to if provided
    reports_to = None
    if request.reports_to_email:
        reports_to = await InternalStakeholder.find_one(
            InternalStakeholder.email == request.reports_to_email
        )
        if not reports_to:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found"
            )
    
    # Create stakeholder
    try:
        stakeholder = await context_manager.get_or_create_internal_stakeholder(
            name=request.name,
            email=request.email,
            role=request.role,
            department=request.department,
            seniority_level=request.seniority_level,
            reports_to=reports_to
        )
        
        logger.info(f"Internal stakeholder created by {current_user.email}: {stakeholder.name} ({stakeholder.email})")
        
        return {
            "status": "success",
            "stakeholder_id": str(stakeholder.id),
            "message": f"Created internal stakeholder: {stakeholder.name}"
        }
        
    except Exception as e:
        logger.error(f"Error creating internal stakeholder: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/stakeholders/access")
async def update_stakeholder_access(
    request: UpdateStakeholderAccessRequest,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Update stakeholder access permissions (requires director+ level)"""
    
    # Check if current user can manage access
    permissions = await access_control.get_user_permissions(current_user)
    if "manage_department" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage access"
        )
    
    # Find target stakeholder
    stakeholder = await InternalStakeholder.find_one(
        InternalStakeholder.email == request.stakeholder_email
    )
    if not stakeholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stakeholder not found"
        )
    
    # Check if current user can modify this stakeholder
    if not await access_control.can_user_assign_role(current_user, stakeholder, request.seniority_level or stakeholder.seniority_level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify this stakeholder's access"
        )
    
    # Update access level
    if not stakeholder.access_level:
        stakeholder.access_level = AccessLevel(level=stakeholder.seniority_level)
    
    if request.seniority_level:
        stakeholder.seniority_level = request.seniority_level
        stakeholder.access_level.level = request.seniority_level
    
    if request.permissions:
        stakeholder.access_level.permissions = request.permissions
    
    if request.can_view_clients:
        stakeholder.access_level.can_view_clients = request.can_view_clients
    
    if request.can_view_projects:
        stakeholder.access_level.can_view_projects = request.can_view_projects
    
    if request.data_access_level:
        stakeholder.access_level.data_access_level = request.data_access_level
    
    await stakeholder.save()
    
    logger.info(f"Stakeholder access updated by {current_user.email}: {stakeholder.name}")
    
    return {
        "status": "success",
        "message": f"Updated access for {stakeholder.name}"
    }

@router.post("/projects/{project_id}/manual-assignment")
async def manual_team_assignment(
    project_id: str,
    request: ProjectAssignmentRequest,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Manually assign stakeholder to project (enhanced with seniority validation)"""
    
    # Find project
    try:
        project = await Project.get(project_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if current user can add team members to this project
    if not await access_control.can_user_add_team_member(current_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add team members to this project"
        )
    
    # Find stakeholder to assign
    stakeholder = await InternalStakeholder.find_one(
        InternalStakeholder.email == request.stakeholder_email
    )
    if not stakeholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stakeholder not found"
        )
    
    # Enhanced seniority validation
    current_user_seniority = access_control.SENIORITY_HIERARCHY.get(current_user.seniority_level, 0)
    stakeholder_seniority = access_control.SENIORITY_HIERARCHY.get(stakeholder.seniority_level, 0)
    
    # Can only assign people of equal or lower seniority
    if stakeholder_seniority > current_user_seniority:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign someone more senior than you ({stakeholder.seniority_level} > {current_user.seniority_level})"
        )
    
    # Check if current user can assign this specific role
    if not await access_control.can_user_assign_role(current_user, stakeholder, request.role_in_project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign role '{request.role_in_project}' to {stakeholder.seniority_level} level person"
        )
    
    # Additional department-based restrictions for cross-department assignments
    if current_user.department != stakeholder.department:
        # Only managers+ can do cross-department assignments
        permissions = await access_control.get_user_permissions(current_user)
        if "manage_team_assignments" not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign people from other departments (requires manager+ level)"
            )
    
    # Create assignment with enhanced permissions
    assignment = await context_manager.get_or_create_project_assignment(
        internal_stakeholder=stakeholder,
        project=project,
        role_in_project=request.role_in_project,
        allocation_percentage=request.allocation_percentage,
        can_view_sensitive_data=request.can_view_sensitive_data,
        can_modify_project=request.can_modify_project,
        can_add_team_members=request.can_add_team_members
    )
    
    logger.info(f"Manual assignment created by {current_user.email}: {stakeholder.name} -> {project.name} as {request.role_in_project}")
    
    return {
        "status": "success",
        "assignment_id": str(assignment.id),
        "message": f"Manually assigned {stakeholder.name} to {project.name} as {request.role_in_project}",
        "assignment_details": {
            "stakeholder": {
                "name": stakeholder.name,
                "email": stakeholder.email,
                "seniority_level": stakeholder.seniority_level,
                "department": stakeholder.department
            },
            "project": {
                "name": project.name,
                "id": str(project.id)
            },
            "role": request.role_in_project,
            "assigned_by": {
                "name": current_user.name,
                "email": current_user.email,
                "seniority_level": current_user.seniority_level
            }
        }
    }

@router.get("/my-permissions")
async def get_my_permissions(
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Get current user's permissions and accessible resources"""
    
    permissions = await access_control.get_user_permissions(current_user)
    accessible_clients = await access_control.get_accessible_clients(current_user)
    accessible_projects = await access_control.get_accessible_projects(current_user)
    
    return {
        "user": {
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "seniority_level": current_user.seniority_level,
            "department": current_user.department
        },
        "permissions": list(permissions),
        "data_access_level": current_user.access_level.data_access_level if current_user.access_level else "basic",
        "accessible_clients": [
            {"id": str(client.id), "name": client.name} 
            for client in accessible_clients
        ],
        "accessible_projects": [
            {"id": str(project.id), "name": project.name} 
            for project in accessible_projects
        ]
    }

@router.get("/projects")
async def list_projects(
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """List all projects the user can access"""
    projects = await access_control.get_accessible_projects(current_user)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "client_name": (await p.client.fetch()).name if p.client else "Unknown"
        }
        for p in projects
    ]

@router.get("/clients")
async def list_clients(
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """List all clients the user can access"""
    clients = await access_control.get_accessible_clients(current_user)
    return [
        {"id": str(c.id), "name": c.name}
        for c in clients
    ]

@router.get("/stakeholders")
async def list_stakeholders(
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """List stakeholders (filtered by access level)"""
    
    permissions = await access_control.get_user_permissions(current_user)
    
    # Only managers+ can view all stakeholders
    if "view_team_performance" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view stakeholders"
        )
    
    # Get stakeholders based on access level
    if "view_everything" in permissions:
        # Executives see everyone
        stakeholders = await InternalStakeholder.find().to_list()
    elif "manage_department" in permissions:
        # Directors see their department
        stakeholders = await InternalStakeholder.find(
            InternalStakeholder.department == current_user.department
        ).to_list()
    else:
        # Managers see their direct reports and peers
        stakeholders = await InternalStakeholder.find(
            InternalStakeholder.reports_to.id == current_user.id
        ).to_list()
        
        # Add peers (same manager)
        if current_user.reports_to:
            peers = await InternalStakeholder.find(
                InternalStakeholder.reports_to.id == current_user.reports_to.id
            ).to_list()
            stakeholders.extend(peers)
    
    return {
        "stakeholders": [
            {
                "id": str(s.id),
                "name": s.name,
                "email": s.email,
                "role": s.role,
                "department": s.department,
                "seniority_level": s.seniority_level,
                "active": s.active
            }
            for s in stakeholders
        ]
    }

@router.post("/access-rules")
async def create_access_rule(
    request: AccessControlRuleRequest,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Create access control rule (requires executive level)"""
    
    permissions = await access_control.get_user_permissions(current_user)
    if "manage_everything" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create access rules"
        )
    
    rule = AccessControlRule(
        rule_name=request.rule_name,
        rule_type=request.rule_type,
        applies_to_roles=request.applies_to_roles or [],
        applies_to_seniority=request.applies_to_seniority or [],
        applies_to_departments=request.applies_to_departments or [],
        permissions=request.permissions,
        data_access_levels=request.data_access_levels or [],
        restricted_clients=request.restricted_clients or [],
        restricted_projects=request.restricted_projects or [],
        created_by=current_user
    )
    
    await rule.insert()
    
    logger.info(f"Access control rule created by {current_user.email}: {rule.rule_name}")
    
    return {
        "status": "success",
        "rule_id": str(rule.id),
        "message": f"Created access rule: {rule.rule_name}"
    }

@router.get("/projects/{project_id}/available-members")
async def get_available_team_members(
    project_id: str,
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Get list of stakeholders that can be assigned to this project"""
    
    # Find project
    try:
        project = await Project.get(project_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if current user can add team members
    if not await access_control.can_user_add_team_member(current_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view available team members for this project"
        )
    
    # Get current user's seniority level
    current_user_seniority = access_control.SENIORITY_HIERARCHY.get(current_user.seniority_level, 0)
    
    # Get all stakeholders that can be assigned
    all_stakeholders = await InternalStakeholder.find(
        InternalStakeholder.active == True
    ).to_list()
    
    available_members = []
    for stakeholder in all_stakeholders:
        stakeholder_seniority = access_control.SENIORITY_HIERARCHY.get(stakeholder.seniority_level, 0)
        
        # Can only assign people of equal or lower seniority
        if stakeholder_seniority <= current_user_seniority:
            # Check if already assigned to this project
            existing_assignment = await ProjectAssignment.find_one(
                ProjectAssignment.internal_stakeholder.id == stakeholder.id,
                ProjectAssignment.project.id == project.id,
                ProjectAssignment.active == True
            )
            
            available_members.append({
                "id": str(stakeholder.id),
                "name": stakeholder.name,
                "email": stakeholder.email,
                "role": stakeholder.role,
                "department": stakeholder.department,
                "seniority_level": stakeholder.seniority_level,
                "already_assigned": existing_assignment is not None,
                "current_role_in_project": existing_assignment.role_in_project if existing_assignment else None,
                "can_assign_roles": [
                    role for role in ["Developer", "Senior Developer", "Lead", "Manager", "Director"]
                    if await access_control.can_user_assign_role(current_user, stakeholder, role)
                ]
            })
    
    return {
        "project": {
            "id": str(project.id),
            "name": project.name
        },
        "available_members": available_members,
        "assignment_permissions": {
            "can_assign_cross_department": "manage_team_assignments" in await access_control.get_user_permissions(current_user),
            "max_assignable_seniority": current_user.seniority_level,
            "current_user_seniority_level": current_user_seniority
        }
    }

@router.get("/hierarchy")
async def get_organization_hierarchy(
    current_user: InternalStakeholder = Depends(get_current_stakeholder)
):
    """Get organization hierarchy (requires manager+ level)"""
    
    permissions = await access_control.get_user_permissions(current_user)
    if "view_team_performance" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view hierarchy"
        )
    
    # Build hierarchy tree
    all_stakeholders = await InternalStakeholder.find(
        InternalStakeholder.active == True
    ).to_list()
    
    # Create hierarchy structure
    hierarchy = {}
    for stakeholder in all_stakeholders:
        manager_id = str(stakeholder.reports_to.id) if stakeholder.reports_to else "root"
        
        if manager_id not in hierarchy:
            hierarchy[manager_id] = []
        
        hierarchy[manager_id].append({
            "id": str(stakeholder.id),
            "name": stakeholder.name,
            "email": stakeholder.email,
            "role": stakeholder.role,
            "seniority_level": stakeholder.seniority_level,
            "department": stakeholder.department
        })
    
    return {"hierarchy": hierarchy}