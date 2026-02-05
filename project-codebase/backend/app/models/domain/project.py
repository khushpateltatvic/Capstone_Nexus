"""
Project and Client Models with RBAC Support
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from .sections import (
    UniversalContext, Operations, TechnicalIntelligence, 
    Commercial, Strategy, Marketing, Other
)
from .permissions import DelegatedPermission, PermissionLevel


class ProjectAccess(BaseModel):
    """RBAC access control for a project"""
    assigned_users: List[str] = []  # User emails with basic access
    delegated_permissions: List[Dict[str, Any]] = []  # Serialized DelegatedPermission
    
    # Override default section access for this project
    section_overrides: Dict[str, Dict[str, str]] = {}  # section -> {role: permission_level}
    
    # Override sensitive field access for this project
    sensitive_field_overrides: Dict[str, List[str]] = {}  # field -> [roles that can view]


class Project(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    
    # RBAC Fields
    created_by: Optional[str] = None  # User email who created
    department: Optional[str] = None  # Primary department
    
    # Access Control
    access: ProjectAccess = Field(default_factory=ProjectAccess)
    
    # The 7 Sections (One of each per project)
    universal_context: UniversalContext = Field(default_factory=UniversalContext)
    operations: Operations = Field(default_factory=Operations)
    technical: TechnicalIntelligence = Field(default_factory=TechnicalIntelligence)
    commercial: Commercial = Field(default_factory=Commercial)
    strategy: Strategy = Field(default_factory=Strategy)
    marketing: Marketing = Field(default_factory=Marketing)
    other: Other = Field(default_factory=Other)
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Client(BaseModel):
    client_id: str
    name: str
    projects: List[Project] = []
    
    # Client-level rollups could go here if needed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
