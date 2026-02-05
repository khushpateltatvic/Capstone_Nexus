from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import Document, Link, Indexed
from pydantic import Field, BaseModel
from pymongo import IndexModel, ASCENDING
from .core_entities import Client, Project

class DocumentSource(BaseModel):
    """Embedded document for tracking source references"""
    source_type: str  # "email", "document", "presentation", "spreadsheet", "basecamp", "slack", "meeting", "manual"
    source_id: Optional[str] = None  # External ID (email thread ID, doc ID, etc.)
    source_url: Optional[str] = None  # Direct link to source
    source_title: Optional[str] = None  # Title/subject of source
    source_date: Optional[datetime] = None  # When the source was created
    extracted_at: datetime = Field(default_factory=datetime.utcnow)  # When we extracted from this source
    metadata: Optional[Dict[str, Any]] = None  # Additional source-specific data

class AccessLevel(BaseModel):
    """Access control configuration"""
    level: str  # "junior", "senior", "lead", "manager", "director", "executive"
    permissions: List[str] = Field(default_factory=list)  # Specific permissions
    can_view_clients: List[str] = Field(default_factory=list)  # Client IDs they can access
    can_view_projects: List[str] = Field(default_factory=list)  # Project IDs they can access
    data_access_level: str = "basic"  # "basic", "detailed", "sensitive", "executive"

class InternalStakeholder(Document):
    """Internal team members working on client projects"""
    name: str  # NOT unique - multiple people can have same name
    email: Indexed(str, unique=True)  # Email is unique identifier
    employee_id: Optional[str] = None  # Company employee ID
    role: str  # "Account Manager", "Technical Lead", "Project Manager", "Developer", "Designer", etc.
    department: Optional[str] = None  # "Engineering", "Sales", "Marketing", "Operations"
    
    # Hierarchy and Access Control
    seniority_level: str = "junior"  # "junior", "senior", "lead", "manager", "director", "executive"
    reports_to: Optional[Link["InternalStakeholder"]] = None  # Manager/supervisor
    access_level: AccessLevel = Field(default_factory=lambda: AccessLevel(level="junior"))
    
    # Status and metadata
    active: bool = True
    hire_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "internal_stakeholders"

class ClientStakeholder(Document):
    """Client-side stakeholders"""
    name: str  # NOT unique - multiple people can have same name
    client: Link[Client]
    email: Optional[str] = None  # Not unique across clients
    phone: Optional[str] = None
    role: str  # "CTO", "Project Manager", "Business Analyst", etc.
    department: Optional[str] = None
    
    # Influence and relationship
    influence_level: str = "Medium"  # High | Medium | Low
    sentiment: str = "Neutral"  # Champion | Supporter | Neutral | Skeptic | Blocker
    decision_maker: bool = False  # Can they make final decisions?
    budget_authority: bool = False  # Do they control budget?
    reports_to: Optional[Link["ClientStakeholder"]] = None  # Hierarchy support
    
    # Contact preferences and metadata
    preferred_contact_method: str = "email"  # email | phone | slack | teams
    timezone: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contact: Optional[datetime] = None
    
    # Source tracking
    sources: List[DocumentSource] = Field(default_factory=list)
    
    class Settings:
        name = "client_stakeholders"

class ProjectAssignment(Document):
    """Track which internal stakeholders are assigned to which projects"""
    internal_stakeholder: Link[InternalStakeholder]
    project: Link[Project]
    role_in_project: str  # "Lead", "Developer", "Reviewer", "Consultant"
    allocation_percentage: Optional[float] = None  # 0-100
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    active: bool = True
    
    # Access control for this specific assignment
    can_view_sensitive_data: bool = False
    can_modify_project: bool = False
    can_add_team_members: bool = False
    
    # Granular Custom Access (Overrides Role Matrix)
    # Stores list of section keys e.g. ["1_universal", "2_ops"]
    custom_view_access: List[str] = Field(default_factory=list)
    custom_edit_access: List[str] = Field(default_factory=list)
    
    # Source tracking
    sources: List[DocumentSource] = Field(default_factory=list)
    
    class Settings:
        name = "project_assignments"

class AccessControlRule(Document):
    """Flexible access control rules"""
    rule_name: str
    rule_type: str  # "role_based", "client_based", "project_based", "data_type_based"
    
    # Conditions
    applies_to_roles: List[str] = Field(default_factory=list)
    applies_to_seniority: List[str] = Field(default_factory=list)
    applies_to_departments: List[str] = Field(default_factory=list)
    
    # Permissions granted
    permissions: List[str] = Field(default_factory=list)
    data_access_levels: List[str] = Field(default_factory=list)
    
    # Restrictions
    restricted_clients: List[str] = Field(default_factory=list)  # Client IDs
    restricted_projects: List[str] = Field(default_factory=list)  # Project IDs
    restricted_data_types: List[str] = Field(default_factory=list)  # "financial", "strategic", "personal"
    
    active: bool = True
    created_by: Link[InternalStakeholder]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "access_control_rules"

class DocumentReference(Document):
    """Central registry for all documents/sources referenced in the system"""
    source_type: str  # "email", "document", "presentation", "spreadsheet", "basecamp", "slack", "meeting"
    source_id: str  # External ID
    source_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    
    # Context associations
    client: Optional[Link[Client]] = None
    project: Optional[Link[Project]] = None
    internal_stakeholders: List[Link[InternalStakeholder]] = Field(default_factory=list)
    client_stakeholders: List[Link[ClientStakeholder]] = Field(default_factory=list)
    
    # Access control
    sensitivity_level: str = "public"  # "public", "internal", "confidential", "restricted"
    access_restricted_to: List[Link[InternalStakeholder]] = Field(default_factory=list)
    
    # Metadata
    created_date: Optional[datetime] = None  # When the original document was created
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "document_references"

class ExternalStakeholder(Document):
    """External stakeholders tied to a specific project (POCs, Influencers, etc.)"""
    project: Link[Project]
    name: str
    role: str # "POC", "CIO", "Technical Manager", etc.
    category: str = "General" # "POC" | "Decision Maker" | "Influencer" | "Other"
    email: Optional[str] = None
    phone: Optional[str] = None
    sentiment: str = "Neutral"
    influence: str = "Medium"
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "external_stakeholders"
        indexes = [
            IndexModel([("project", ASCENDING), ("name", ASCENDING)], unique=True)
        ]