"""
Permission Models for RBAC

Defines permission levels, section permissions, and delegated permissions.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class PermissionLevel(str, Enum):
    """Permission levels for section access"""
    NONE = "none"      # Cannot access
    VIEW = "view"      # Read only
    EDIT = "edit"      # Can add/update
    FULL = "full"      # Full CRUD including delete


# Permission level hierarchy for comparison
PERMISSION_HIERARCHY = [
    PermissionLevel.NONE,
    PermissionLevel.VIEW,
    PermissionLevel.EDIT,
    PermissionLevel.FULL,
]


def get_permission_level(level: PermissionLevel) -> int:
    """Get numeric level for permission comparison"""
    try:
        return PERMISSION_HIERARCHY.index(level)
    except ValueError:
        return 0


def has_min_permission(user_level: PermissionLevel, required_level: PermissionLevel) -> bool:
    """Check if user has at least the required permission level"""
    return get_permission_level(user_level) >= get_permission_level(required_level)


class SectionPermission(BaseModel):
    """Permission settings for a specific section"""
    section: str  # universal_context, operations, commercial, etc.
    level: PermissionLevel = PermissionLevel.VIEW
    fields_hidden: List[str] = []  # Fields to hide within this section


class DelegatedPermission(BaseModel):
    """Permission delegated by a senior to a junior user"""
    user_email: str
    granted_by: str  # Senior who granted this permission
    sections: List[SectionPermission] = []
    expires_at: Optional[datetime] = None
    status: str = "active"  # active, pending_approval, revoked
    created_at: datetime = datetime.utcnow()
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class DelegatePermissionRequest(BaseModel):
    """Request to delegate permissions to a user"""
    user_email: str
    sections: List[SectionPermission]
    expires_at: Optional[datetime] = None
    requires_approval: bool = False
    notes: Optional[str] = None


class AssignUserRequest(BaseModel):
    """Request to assign a user to a project"""
    user_email: str
    sections: Optional[List[SectionPermission]] = None  # If None, use defaults


class UpdatePermissionRequest(BaseModel):
    """Request to update user's permissions"""
    sections: List[SectionPermission]
    expires_at: Optional[datetime] = None


# Default section access by role
DEFAULT_SECTION_ACCESS: Dict[str, Dict[str, PermissionLevel]] = {
    "universal_context": {
        "trainee": PermissionLevel.VIEW,
        "analyst": PermissionLevel.VIEW,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "operations": {
        "trainee": PermissionLevel.VIEW,
        "analyst": PermissionLevel.EDIT,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "technical": {
        "trainee": PermissionLevel.VIEW,
        "analyst": PermissionLevel.EDIT,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "commercial": {
        "trainee": PermissionLevel.NONE,
        "analyst": PermissionLevel.NONE,
        "lead": PermissionLevel.VIEW,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "strategy": {
        "trainee": PermissionLevel.NONE,
        "analyst": PermissionLevel.VIEW,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "marketing": {
        "trainee": PermissionLevel.VIEW,
        "analyst": PermissionLevel.VIEW,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
    "other": {
        "trainee": PermissionLevel.VIEW,
        "analyst": PermissionLevel.EDIT,
        "lead": PermissionLevel.EDIT,
        "head": PermissionLevel.FULL,
        "admin": PermissionLevel.FULL,
        "director": PermissionLevel.FULL,
    },
}

# Fields that require special access (role -> can view)
SENSITIVE_FIELDS: Dict[str, List[str]] = {
    "stakeholder_map": ["lead", "head", "admin", "director"],
    "stakeholder_hierarchy": ["lead", "head", "admin", "director"],
    "financial_overview": ["head", "admin", "director"],
    "invoices": ["head", "admin", "director"],
    "access_credentials": ["analyst", "lead", "head", "admin", "director"],
    "contract_value": ["head", "admin", "director"],
}
