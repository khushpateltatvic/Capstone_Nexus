"""
Project API Endpoints with RBAC

Provides CRUD operations for projects with role-based access control:
- GET /projects - List projects user has access to
- GET /projects/{client_id} - List client projects user can access
- GET /projects/{client_id}/{project_id} - Get project (if assigned)
- POST /projects - Create project (Head/Admin/Director only)
- PUT /projects/{client_id}/{project_id} - Update project (Head/Admin/Director only)
- DELETE /projects/{client_id}/{project_id} - Delete project (Head/Admin/Director only)

Permission Management:
- GET /projects/{client_id}/{project_id}/permissions - List permissions
- POST /projects/{client_id}/{project_id}/permissions/assign - Assign user
- POST /projects/{client_id}/{project_id}/permissions/delegate - Delegate to junior
- PUT /projects/{client_id}/{project_id}/permissions/{email} - Update permissions
- DELETE /projects/{client_id}/{project_id}/permissions/{email} - Remove access
- POST /projects/{client_id}/{project_id}/permissions/approve/{email} - Approve pending
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User, UserRole
from app.models.domain.permissions import (
    PermissionLevel, 
    SectionPermission,
    DelegatedPermission,
    DelegatePermissionRequest,
    AssignUserRequest,
    UpdatePermissionRequest,
    DEFAULT_SECTION_ACCESS
)
from app.core.rbac import (
    is_admin_role,
    is_senior_to,
    has_project_access,
    get_effective_section_permission,
    get_user_by_email,
    VALID_SECTIONS
)

router = APIRouter()


# --- Request/Response Models ---

class ProjectCreate(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    assigned_users: List[str] = []  # Initial user assignments


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department: Optional[str] = None


class ProjectSummary(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    created_by: Optional[str] = None
    sections_populated: List[str] = []
    assigned_users_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProjectDetail(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    department: Optional[str] = None
    created_by: Optional[str] = None
    access: Dict[str, Any] = {}
    universal_context: Dict[str, Any] = {}
    operations: Dict[str, Any] = {}
    technical: Dict[str, Any] = {}
    commercial: Dict[str, Any] = {}
    strategy: Dict[str, Any] = {}
    marketing: Dict[str, Any] = {}
    other: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    user_permissions: Dict[str, str] = {}  # section -> permission level for current user


class PermissionInfo(BaseModel):
    user_email: str
    role: Optional[str] = None  # User's role from users collection (for logic)
    job_title: Optional[str] = None  # User's job title (for display)
    type: str  # "assigned" or "delegated"
    sections: List[Dict[str, Any]] = []
    granted_by: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None


SECTIONS = ["universal_context", "operations", "technical", "commercial", "strategy", "marketing", "other"]


def get_populated_sections(doc: dict) -> List[str]:
    """Returns list of section names that have data."""
    populated = []
    for section in SECTIONS:
        section_data = doc.get(section, {})
        if section_data and any(v for v in section_data.values() if v):
            populated.append(section)
    return populated


# --- Project CRUD Endpoints ---

@router.get("", response_model=List[ProjectSummary])
async def list_all_projects(
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all projects the user has access to.
    - Admins see all projects in their department
    - Others see only assigned projects
    """
    db = await get_database()
    
    query = {}
    if client_id:
        query["client_id"] = client_id
    
    projects = []
    async for doc in db.projects.find(query):
        # Check if user has access
        if not has_project_access(current_user, doc):
            continue
            
        access = doc.get("access", {})
        projects.append(ProjectSummary(
            project_id=doc.get("project_id"),
            client_id=doc.get("client_id"),
            name=doc.get("name", doc.get("project_id")),
            description=doc.get("description"),
            department=doc.get("department"),
            created_by=doc.get("created_by"),
            sections_populated=get_populated_sections(doc),
            assigned_users_count=len(access.get("assigned_users", [])),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at")
        ))
    
    return projects


@router.get("/{client_id}", response_model=List[ProjectSummary])
async def list_client_projects(
    client_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all projects for a client that user can access."""
    db = await get_database()
    
    projects = []
    async for doc in db.projects.find({"client_id": client_id}):
        if not has_project_access(current_user, doc):
            continue
            
        access = doc.get("access", {})
        projects.append(ProjectSummary(
            project_id=doc.get("project_id"),
            client_id=doc.get("client_id"),
            name=doc.get("name", doc.get("project_id")),
            description=doc.get("description"),
            department=doc.get("department"),
            created_by=doc.get("created_by"),
            sections_populated=get_populated_sections(doc),
            assigned_users_count=len(access.get("assigned_users", [])),
            created_at=doc.get("created_at"),
            updated_at=doc.get("updated_at")
        ))
    
    return projects


@router.get("/{client_id}/{project_id}", response_model=ProjectDetail)
async def get_project(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get project details with section data filtered by user permissions."""
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        # Relax constraint: try finding by project_id alone (common if client_id from URL is generic/wrong)
        doc = await db.projects.find_one({"project_id": project_id})
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Calculate user's permissions for each section
    user_permissions = {}
    for section in SECTIONS:
        perm = get_effective_section_permission(current_user, doc, section)
        user_permissions[section] = perm.value
    
    # Filter sections based on permissions (hide sections with "none" permission)
    from app.core.rbac import filter_sensitive_fields
    
    response_data = {
        "project_id": doc.get("project_id"),
        "client_id": doc.get("client_id"),
        "name": doc.get("name", doc.get("project_id")),
        "description": doc.get("description"),
        "department": doc.get("department"),
        "created_by": doc.get("created_by"),
        "access": doc.get("access", {}) if is_admin_role(current_user) else {},
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "user_permissions": user_permissions,
    }
    
    # Add section data filtered by permission
    for section in SECTIONS:
        perm = get_effective_section_permission(current_user, doc, section)
        if perm == PermissionLevel.NONE:
            response_data[section] = {}  # Hide entire section
        else:
            section_data = doc.get(section, {})
            response_data[section] = filter_sensitive_fields(current_user, doc, section, section_data)
    
    return ProjectDetail(**response_data)


@router.post("", response_model=ProjectSummary, status_code=201)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new project. Requires Head/Admin/Director role."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403, 
            detail="Only Head, Admin, or Director roles can create projects"
        )
    
    db = await get_database()
    
    # Check if project already exists
    existing = await db.projects.find_one({
        "client_id": payload.client_id,
        "project_id": payload.project_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")
    
    now = datetime.utcnow().isoformat()
    project_doc = {
        "project_id": payload.project_id,
        "client_id": payload.client_id,
        "name": payload.name,
        "description": payload.description,
        "department": payload.department or current_user.department,
        "created_by": current_user.email,
        "access": {
            "assigned_users": payload.assigned_users,
            "delegated_permissions": [],
            "section_overrides": {},
            "sensitive_field_overrides": {}
        },
        "universal_context": {},
        "operations": {},
        "technical": {},
        "commercial": {},
        "strategy": {},
        "marketing": {},
        "other": {},
        "created_at": now,
        "updated_at": now
    }
    
    await db.projects.insert_one(project_doc)
    
    # Ensure client exists
    await db.clients.update_one(
        {"client_id": payload.client_id},
        {"$setOnInsert": {
            "client_id": payload.client_id,
            "name": payload.client_id,
            "created_at": now
        }},
        upsert=True
    )
    
    return ProjectSummary(
        project_id=payload.project_id,
        client_id=payload.client_id,
        name=payload.name,
        description=payload.description,
        department=project_doc["department"],
        created_by=current_user.email,
        sections_populated=[],
        assigned_users_count=len(payload.assigned_users),
        created_at=now,
        updated_at=now
    )


@router.put("/{client_id}/{project_id}", response_model=ProjectSummary)
async def update_project(
    client_id: str,
    project_id: str,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update project metadata. Requires Head/Admin/Director role."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Head, Admin, or Director roles can update projects"
        )
    
    db = await get_database()
    
    # Verify project exists and user has access
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Build update dict
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": update_data}
    )
    
    # Fetch updated doc
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    access = doc.get("access", {})
    return ProjectSummary(
        project_id=doc.get("project_id"),
        client_id=doc.get("client_id"),
        name=doc.get("name", doc.get("project_id")),
        description=doc.get("description"),
        department=doc.get("department"),
        created_by=doc.get("created_by"),
        sections_populated=get_populated_sections(doc),
        assigned_users_count=len(access.get("assigned_users", [])),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at")
    )


@router.delete("/{client_id}/{project_id}")
async def delete_project(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a project. Requires Head/Admin/Director role."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Head, Admin, or Director roles can delete projects"
        )
    
    db = await get_database()
    
    # Verify project exists and user has access
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    result = await db.projects.delete_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    return {
        "status": "deleted",
        "client_id": client_id,
        "project_id": project_id
    }


# --- Permission Management Endpoints ---

@router.get("/{client_id}/{project_id}/permissions", response_model=List[PermissionInfo])
async def list_project_permissions(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all permissions for a project. Requires admin role or project access."""
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    access = doc.get("access", {})
    permissions = []
    processed_emails = set()
    
    # Collect all unique user emails
    user_emails = set()
    user_emails.update(access.get("assigned_users", []))
    user_emails.update([perm.get("user_email") for perm in access.get("delegated_permissions", [])])
    
    # Fetch all user roles and job titles in one query
    user_data = {}
    if user_emails:
        users_cursor = db.users.find({"email": {"$in": list(user_emails)}})
        async for user_doc in users_cursor:
            user_data[user_doc["email"]] = {
                "role": user_doc.get("role", "trainee"),
                "job_title": user_doc.get("job_title")
            }
    
    # Add delegated permissions first
    for perm in access.get("delegated_permissions", []):
        email = perm.get("user_email")
        if email:
            user_info = user_data.get(email, {})
            permissions.append(PermissionInfo(
                user_email=email,
                role=user_info.get("role"),
                job_title=user_info.get("job_title"),
                type="delegated",
                sections=perm.get("sections", []),
                granted_by=perm.get("granted_by"),
                status=perm.get("status"),
                expires_at=perm.get("expires_at")
            ))
            processed_emails.add(email)
    
    # Add assigned users only if they're not already in delegated permissions
    for email in access.get("assigned_users", []):
        if email not in processed_emails:
            user_info = user_data.get(email, {})
            
            # Combined PermissionInfo with all necessary fields
            permissions.append(PermissionInfo(
                user_email=email,
                role=user_info.get("role"),
                job_title=user_info.get("job_title"),
                type="assigned",
                sections=[],
                status="active"
            ))
    
    return permissions


@router.post("/{client_id}/{project_id}/permissions/assign")
async def assign_user_to_project(
    client_id: str,
    project_id: str,
    payload: AssignUserRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Assign a user to the project with default role-based permissions."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Head, Admin, or Director roles can assign users"
        )
    
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Verify user exists
    target_user = await get_user_by_email(payload.user_email)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add to assigned users
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$addToSet": {"access.assigned_users": payload.user_email},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return {
        "status": "success",
        "message": f"User {payload.user_email} assigned to project",
        "user_email": payload.user_email
    }


@router.post("/{client_id}/{project_id}/permissions/delegate")
async def delegate_permissions(
    client_id: str,
    project_id: str,
    payload: DelegatePermissionRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delegate specific section permissions to a junior user.
    Seniors can grant their juniors additional permissions.
    """
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Verify target user exists
    target_user = await get_user_by_email(payload.user_email)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Check if current user is senior to target user
    if not is_senior_to(current_user, target_user):
        raise HTTPException(
            status_code=403,
            detail="You can only delegate permissions to users with lower roles"
        )
    
    # Validate that delegator has the permissions they're granting
    for section_perm in payload.sections:
        if section_perm.section not in VALID_SECTIONS:
            raise HTTPException(status_code=400, detail=f"Invalid section: {section_perm.section}")
        
        delegator_perm = get_effective_section_permission(current_user, doc, section_perm.section)
        if delegator_perm.value == "none":
            raise HTTPException(
                status_code=403,
                detail=f"You don't have access to section '{section_perm.section}'"
            )
    
    # Create delegation record
    delegation = {
        "user_email": payload.user_email,
        "granted_by": current_user.email,
        "sections": [sp.dict() for sp in payload.sections],
        "expires_at": payload.expires_at.isoformat() if payload.expires_at else None,
        "status": "pending_approval" if payload.requires_approval else "active",
        "created_at": datetime.utcnow().isoformat(),
        "approved_at": None if payload.requires_approval else datetime.utcnow().isoformat(),
        "notes": payload.notes
    }
    
    # Remove any existing delegation for this user
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$pull": {"access.delegated_permissions": {"user_email": payload.user_email}}}
    )
    
    # Add new delegation (delegated users don't need to be in assigned_users)
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$push": {"access.delegated_permissions": delegation},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return {
        "status": "success",
        "message": f"Permissions delegated to {payload.user_email}",
        "delegation": delegation
    }


@router.put("/{client_id}/{project_id}/permissions/{email}")
async def update_user_permissions(
    client_id: str,
    project_id: str,
    email: str,
    payload: UpdatePermissionRequest,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a user's delegated permissions."""
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Check permission to update
    target_user = await get_user_by_email(email)
    if target_user and not is_senior_to(current_user, target_user) and not is_admin_role(current_user):
        raise HTTPException(status_code=403, detail="Cannot update permissions for this user")
    
    # Update delegation
    update_data = {
        "access.delegated_permissions.$[elem].sections": [sp.dict() for sp in payload.sections],
        "access.delegated_permissions.$[elem].expires_at": payload.expires_at.isoformat() if payload.expires_at else None,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": update_data},
        array_filters=[{"elem.user_email": email}]
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="No delegation found for this user")
    
    return {"status": "success", "message": f"Permissions updated for {email}"}


@router.delete("/{client_id}/{project_id}/permissions/{email}")
async def remove_user_permissions(
    client_id: str,
    project_id: str,
    email: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Remove a user's access to the project."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Head, Admin, or Director roles can remove user access"
        )
    
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Remove from assigned users and delegated permissions
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$pull": {
                "access.assigned_users": email,
                "access.delegated_permissions": {"user_email": email}
            },
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return {"status": "success", "message": f"Access removed for {email}"}


@router.post("/{client_id}/{project_id}/permissions/approve/{email}")
async def approve_pending_permission(
    client_id: str,
    project_id: str,
    email: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Approve a pending permission delegation."""
    if not is_admin_role(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only Head, Admin, or Director roles can approve permissions"
        )
    
    db = await get_database()
    
    doc = await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })
    
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(current_user, doc):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    # Update delegation status
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$set": {
                "access.delegated_permissions.$[elem].status": "active",
                "access.delegated_permissions.$[elem].approved_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        },
        array_filters=[{"elem.user_email": email, "elem.status": "pending_approval"}]
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="No pending approval found for this user")
    
    return {"status": "success", "message": f"Permission approved for {email}"}


# --- Project News Endpoints ---

@router.post("/{client_id}/{project_id}/news/refresh")
async def refresh_project_news(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Fetch and update latest project-specific news (Client + Project Domain/Competitors)."""
    from app.services.intelligence.news_service import fetch_project_news
    
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    news = await fetch_project_news(project_id)
    return {"status": "success", "count": len(news), "data": news}


@router.get("/{client_id}/{project_id}/news")
async def get_project_news(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get stored news for the project."""
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not has_project_access(current_user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")

    return {
        "project_id": project_id,
        "last_updated": project.get("news_last_updated"),
        "data": project.get("news", [])
    }
