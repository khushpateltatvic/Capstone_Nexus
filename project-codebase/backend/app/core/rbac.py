"""
RBAC Core Module

Provides permission checking utilities for role-based access control.
"""

from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from app.models.domain.user import User, UserRole, get_role_level, ROLE_HIERARCHY
from app.models.domain.permissions import (
    PermissionLevel, 
    get_permission_level,
    has_min_permission,
    DEFAULT_SECTION_ACCESS,
    SENSITIVE_FIELDS,
    DelegatedPermission,
)
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user


# Roles that can perform admin operations (CRUD on projects)
ADMIN_ROLES = [UserRole.HEAD, UserRole.ADMIN, UserRole.DIRECTOR]

# Valid sections
VALID_SECTIONS = [
    "universal_context", 
    "operations", 
    "technical", 
    "commercial", 
    "strategy", 
    "marketing", 
    "other"
]


def is_admin_role(user: User) -> bool:
    """Check if user has admin-level role (Head/Admin/Director)"""
    return user.role in ADMIN_ROLES or user.is_superuser


def is_senior_to(senior: User, junior: User) -> bool:
    """Check if senior user has higher role than junior"""
    if senior.is_superuser:
        return True
    return get_role_level(senior.role) > get_role_level(junior.role)


def get_user_department_projects(user: User) -> bool:
    """Check if user can access all projects in their department"""
    return is_admin_role(user)


async def get_project_doc(client_id: str, project_id: str) -> Optional[Dict[str, Any]]:
    """Fetch project document from database"""
    db = await get_database()
    return await db.projects.find_one({
        "client_id": client_id,
        "project_id": project_id
    })


def has_project_access(user: User, project_doc: Dict[str, Any]) -> bool:
    """
    Check if user can access a project.
    
    Access is granted ONLY if:
    1. User is superuser
    2. User is the creator of the project
    3. User is in assigned_users list
    4. User has delegated permission
    
    Note: Admin roles (Head/Admin/Director) must also be in assigned_users
    to access a project, unless they are superuser or creator.
    """
    if user.is_superuser:
        return True
    
    # Check if user is creator
    if project_doc.get("created_by") == user.email:
        return True
    
    # Check assigned users (applies to ALL roles including admins)
    access = project_doc.get("access", {})
    assigned_users = access.get("assigned_users", [])
    if user.email in assigned_users:
        return True
    
    # Check delegated permissions
    delegated = access.get("delegated_permissions", [])
    for perm in delegated:
        if perm.get("user_email") == user.email and perm.get("status") == "active":
            return True
    
    return False


def get_effective_section_permission(
    user: User, 
    project_doc: Dict[str, Any], 
    section: str
) -> PermissionLevel:
    """
    Get the effective permission level for a user on a specific section.
    
    Priority:
    1. Superuser -> FULL
    2. Delegated permissions (if any)
    3. Project-specific section overrides
    4. Default section access by role
    """
    if user.is_superuser:
        return PermissionLevel.FULL
    
    access = project_doc.get("access", {})
    
    # Check delegated permissions first (highest priority for non-superuser)
    delegated = access.get("delegated_permissions", [])
    for perm in delegated:
        if perm.get("user_email") == user.email and perm.get("status") == "active":
            for sec_perm in perm.get("sections", []):
                if sec_perm.get("section") == section:
                    return PermissionLevel(sec_perm.get("level", "view"))
    
    # Check project-specific section overrides
    section_overrides = access.get("section_overrides", {})
    if section in section_overrides:
        role_perms = section_overrides[section]
        role_str = user.role.value if isinstance(user.role, UserRole) else user.role
        if role_str in role_perms:
            return PermissionLevel(role_perms[role_str])
    
    # Fall back to default section access
    role_str = user.role.value if isinstance(user.role, UserRole) else user.role
    default = DEFAULT_SECTION_ACCESS.get(section, {})
    perm_str = default.get(role_str, "none")
    return PermissionLevel(perm_str)


def can_view_field(
    user: User, 
    project_doc: Dict[str, Any], 
    section: str, 
    field: str
) -> bool:
    """
    Check if user can view a specific field within a section.
    
    Returns True if:
    1. User is superuser
    2. Field is not in sensitive fields list
    3. User's role is in the allowed roles for that field
    4. Project has override allowing this role
    """
    if user.is_superuser:
        return True
    
    # Check if field is sensitive
    if field not in SENSITIVE_FIELDS:
        return True
    
    role_str = user.role.value if isinstance(user.role, UserRole) else user.role
    
    # Check project-specific overrides
    access = project_doc.get("access", {})
    field_overrides = access.get("sensitive_field_overrides", {})
    if field in field_overrides:
        return role_str in field_overrides[field]
    
    # Check default sensitive field access
    allowed_roles = SENSITIVE_FIELDS.get(field, [])
    return role_str in allowed_roles


def filter_sensitive_fields(
    user: User, 
    project_doc: Dict[str, Any], 
    section: str, 
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Filter out sensitive fields that the user cannot view.
    """
    if user.is_superuser:
        return data
    
    filtered = {}
    for key, value in data.items():
        if can_view_field(user, project_doc, section, key):
            filtered[key] = value
    
    return filtered


async def require_project_access(
    client_id: str,
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency that checks project access and returns project doc.
    Raises 403 if user doesn't have access, 404 if project not found.
    """
    project_doc = await get_project_doc(client_id, project_id)
    
    if not project_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not has_project_access(current_user, project_doc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )
    
    return project_doc


def require_section_permission(section: str, min_level: PermissionLevel):
    """
    Factory for FastAPI dependency that checks section permission.
    """
    async def dependency(
        client_id: str,
        project_id: str,
        current_user: User = Depends(get_current_user)
    ) -> Dict[str, Any]:
        project_doc = await get_project_doc(client_id, project_id)
        
        if not project_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        if not has_project_access(current_user, project_doc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        
        user_perm = get_effective_section_permission(current_user, project_doc, section)
        if not has_min_permission(user_perm, min_level):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You need at least '{min_level.value}' permission for section '{section}'"
            )
        
        return project_doc
    
    return dependency


def require_admin_role():
    """
    FastAPI dependency that requires admin role (Head/Admin/Director).
    """
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if not is_admin_role(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action requires Head, Admin, or Director role"
            )
        return current_user
    
    return dependency


async def get_user_by_email(email: str) -> Optional[User]:
    """Fetch user by email from database"""
    db = await get_database()
    user_doc = await db.users.find_one({"email": email})
    if user_doc:
        return User(**user_doc)
    return None
