"""
Section API Endpoints with RBAC

Provides CRUD operations for individual project sections with role-based access:
- GET /{client_id}/{project_id}/{section} - Get section (requires view permission)
- PUT /{client_id}/{project_id}/{section} - Replace section (requires edit permission)
- PATCH /{client_id}/{project_id}/{section} - Partial update (requires edit permission)
- DELETE /{client_id}/{project_id}/{section} - Clear section (requires full permission)

Field-level operations with sensitive field filtering:
- GET /{client_id}/{project_id}/{section}/{field} - Get field (checks field visibility)
- PUT /{client_id}/{project_id}/{section}/{field} - Update field (requires edit permission)
- DELETE /{client_id}/{project_id}/{section}/{field} - Delete field (requires full permission)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict
from datetime import datetime
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.models.domain.permissions import PermissionLevel, has_min_permission
from app.core.rbac import (
    has_project_access,
    get_effective_section_permission,
    can_view_field,
    filter_sensitive_fields,
    is_admin_role,
    VALID_SECTIONS
)

router = APIRouter()


async def get_project_with_access_check(
    client_id: str, 
    project_id: str, 
    user: User
) -> Dict[str, Any]:
    """Fetch project and verify user has access."""
    db = await get_database()
    project = await db.projects.find_one({
        "client_id": client_id, 
        "project_id": project_id
    })
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not has_project_access(user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    return project


def check_section_permission(
    user: User, 
    project: Dict[str, Any], 
    section: str, 
    required: PermissionLevel
):
    """Check if user has required permission for section."""
    user_perm = get_effective_section_permission(user, project, section)
    if not has_min_permission(user_perm, required):
        raise HTTPException(
            status_code=403,
            detail=f"You need at least '{required.value}' permission for section '{section}'. You have '{user_perm.value}'."
        )


# --- Section-Level Endpoints ---

@router.get("/{client_id}/{project_id}/{section_name}")
async def get_section(
    client_id: str,
    project_id: str,
    section_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get an entire section's data.
    Sensitive fields are filtered based on user's role.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check view permission
    check_section_permission(current_user, project, section_name, PermissionLevel.VIEW)
    
    section_data = project.get(section_name, {})
    
    # Filter sensitive fields
    filtered_data = filter_sensitive_fields(current_user, project, section_name, section_data)
    
    # Get user's permission level for context
    user_perm = get_effective_section_permission(current_user, project, section_name)
    
    return {
        "client_id": client_id,
        "project_id": project_id,
        "section": section_name,
        "data": filtered_data,
        "field_count": len(filtered_data),
        "permission_level": user_perm.value,
        "can_edit": has_min_permission(user_perm, PermissionLevel.EDIT),
        "can_delete": has_min_permission(user_perm, PermissionLevel.FULL)
    }


@router.put("/{client_id}/{project_id}/{section_name}")
async def replace_section(
    client_id: str,
    project_id: str,
    section_name: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Replace an entire section with new data.
    Requires EDIT permission for the section.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check edit permission
    check_section_permission(current_user, project, section_name, PermissionLevel.EDIT)
    
    db = await get_database()
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$set": {
                section_name: payload,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    return {
        "status": "replaced",
        "section": section_name,
        "field_count": len(payload),
        "updated_by": current_user.email
    }


@router.patch("/{client_id}/{project_id}/{section_name}")
async def partial_update_section(
    client_id: str,
    project_id: str,
    section_name: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Partial update a section (merge with existing data).
    Requires EDIT permission for the section.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check edit permission
    check_section_permission(current_user, project, section_name, PermissionLevel.EDIT)
    
    db = await get_database()
    
    # Build dot-notation update for each field
    update_ops = {f"{section_name}.{k}": v for k, v in payload.items()}
    update_ops["updated_at"] = datetime.utcnow().isoformat()
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": update_ops}
    )
    
    return {
        "status": "updated",
        "section": section_name,
        "fields_updated": list(payload.keys()),
        "updated_by": current_user.email
    }


@router.delete("/{client_id}/{project_id}/{section_name}")
async def clear_section(
    client_id: str,
    project_id: str,
    section_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Clear all data from a section.
    Requires FULL permission for the section.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check full permission (delete requires full access)
    check_section_permission(current_user, project, section_name, PermissionLevel.FULL)
    
    db = await get_database()
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$set": {
                section_name: {},
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    return {
        "status": "cleared", 
        "section": section_name,
        "cleared_by": current_user.email
    }


# --- Field-Level Endpoints ---

@router.get("/{client_id}/{project_id}/{section_name}/{field_name}")
async def get_field(
    client_id: str,
    project_id: str,
    section_name: str,
    field_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific field from a section.
    Checks both section permission and field visibility.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check section view permission
    check_section_permission(current_user, project, section_name, PermissionLevel.VIEW)
    
    # Check field visibility
    if not can_view_field(current_user, project, section_name, field_name):
        raise HTTPException(
            status_code=403,
            detail=f"You don't have permission to view field '{field_name}'"
        )
    
    section_data = project.get(section_name, {})
    
    if field_name not in section_data:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found in {section_name}")
    
    return {
        "client_id": client_id,
        "project_id": project_id,
        "section": section_name,
        "field": field_name,
        "data": section_data[field_name]
    }


@router.put("/{client_id}/{project_id}/{section_name}/{field_name}")
async def update_field(
    client_id: str,
    project_id: str,
    section_name: str,
    field_name: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a specific field in a section.
    Requires EDIT permission for the section.
    
    Payload format: {"value": <data>} or just the data directly
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check edit permission
    check_section_permission(current_user, project, section_name, PermissionLevel.EDIT)
    
    db = await get_database()
    
    # Accept either {"value": data} or raw data
    field_value = payload.get("value", payload)
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$set": {
                f"{section_name}.{field_name}": field_value,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    return {
        "status": "updated",
        "section": section_name,
        "field": field_name,
        "updated_by": current_user.email
    }


@router.delete("/{client_id}/{project_id}/{section_name}/{field_name}")
async def delete_field(
    client_id: str,
    project_id: str,
    section_name: str,
    field_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a specific field from a section.
    Requires FULL permission for the section.
    """
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Check full permission (delete requires full access)
    check_section_permission(current_user, project, section_name, PermissionLevel.FULL)
    
    db = await get_database()
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$unset": {f"{section_name}.{field_name}": ""},
            "$set": {"updated_at": datetime.utcnow().isoformat()}
        }
    )
    
    return {
        "status": "deleted",
        "section": section_name,
        "field": field_name,
        "deleted_by": current_user.email
    }


# --- Section Access Management ---

@router.get("/{client_id}/{project_id}/{section_name}/permissions")
async def get_section_permissions(
    client_id: str,
    project_id: str,
    section_name: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get permission settings for a section. Admin only."""
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    if not is_admin_role(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    access = project.get("access", {})
    section_overrides = access.get("section_overrides", {}).get(section_name, {})
    
    from app.models.domain.permissions import DEFAULT_SECTION_ACCESS
    defaults = DEFAULT_SECTION_ACCESS.get(section_name, {})
    
    return {
        "section": section_name,
        "default_permissions": {k: v.value for k, v in defaults.items()},
        "overrides": section_overrides
    }


@router.put("/{client_id}/{project_id}/{section_name}/permissions")
async def update_section_permissions(
    client_id: str,
    project_id: str,
    section_name: str,
    payload: Dict[str, str],  # {role: permission_level}
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update permission settings for a section. Admin only."""
    if section_name not in VALID_SECTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid section. Must be one of {VALID_SECTIONS}")
    
    if not is_admin_role(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    project = await get_project_with_access_check(client_id, project_id, current_user)
    
    # Validate permission levels
    valid_levels = ["none", "view", "edit", "full"]
    for role, level in payload.items():
        if level not in valid_levels:
            raise HTTPException(status_code=400, detail=f"Invalid permission level: {level}")
    
    db = await get_database()
    
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {
            "$set": {
                f"access.section_overrides.{section_name}": payload,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    )
    
    return {
        "status": "updated",
        "section": section_name,
        "permissions": payload,
        "updated_by": current_user.email
    }
