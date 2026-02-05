"""
Role-Based Access Control (RBAC) System for Project Nexus
Implements hierarchical permissions with proper access levels
"""
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum
from beanie import Document, Link, Indexed
from pydantic import Field, BaseModel, EmailStr
from .core_entities import Client, Project

class AccessLevel(str, Enum):
    """Access levels in hierarchical order (higher = more permissions)"""
    VIEWER = "viewer"                    # Level 1: Read-only access
    CONTRIBUTOR = "contributor"          # Level 2: Can add data, limited edit
    TEAM_LEAD = "team_lead"             # Level 3: Can manage team members
    PROJECT_MANAGER = "project_manager"  # Level 4: Can manage projects
    ACCOUNT_MANAGER = "account_manager"  # Level 5: Can manage clients
    SENIOR_MANAGER = "senior_manager"    # Level 6: Can manage multiple accounts
    HOD = "hod"                         # Level 7: Head of Department
    EXECUTIVE = "executive"              # Level 8: C-level access
    ADMIN = "admin"                     # Level 9: System administrator

class Permission(str, Enum):
    """Granular permissions"""
    # Data permissions
    READ_CLIENT_DATA = "read_client_data"
    WRITE_CLIENT_DATA = "write_client_data"
    DELETE_CLIENT_DATA = "delete_client_data"
    
    # Project permissions
    READ_PROJECT_DATA = "read_project_data"
    WRITE_PROJECT_DATA = "write_project_data"
    DELETE_PROJECT_DATA = "delete_project_data"
    CREATE_PROJECT = "create_project"
    
    # Stakeholder permissions
    READ_STAKEHOLDERS = "read_stakeholders"
    WRITE_STAKEHOLDERS = "write_stakeholders"
    DELETE_STAKEHOLDERS = "delete_stakeholders"
    
    # User management permissions
    READ_USERS = "read_users"
    CREATE_USER = "create_user"
    MODIFY_USER = "modify_user"
    DELETE_USER = "delete_user"
    ASSIGN_ROLES = "assign_roles"
    
    # Financial permissions
    READ_FINANCIAL = "read_financial"
    WRITE_FINANCIAL = "write_financial"
    
    # System permissions
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOGS = "audit_logs"

class Department(str, Enum):
    """Company departments"""
    ENGINEERING = "engineering"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    HR = "hr"
    EXECUTIVE = "executive"

class RoleDefinition(Document):
    """Define roles with their permissions and access levels"""
    name: str
    access_level: AccessLevel
    permissions: List[Permission]
    description: Optional[str] = None
    can_create_roles: List[AccessLevel] = Field(default_factory=list)  # Which roles this role can create
    max_assignable_level: Optional[AccessLevel] = None  # Highest level this role can assign
    
    class Settings:
        name = "role_definitions"

class EnhancedUser(Document):
    """Enhanced user model with RBAC"""
    # Basic info
    email: Indexed(EmailStr, unique=True)
    hashed_password: str
    full_name: str
    employee_id: Optional[str] = None  # Company employee ID
    
    # Identity matching fields
    phone: Optional[str] = None
    alternate_email: Optional[str] = None
    linkedin_profile: Optional[str] = None
    
    # Role and access
    role: Link[RoleDefinition]
    department: Department
    access_level: AccessLevel
    custom_permissions: List[Permission] = Field(default_factory=list)  # Additional permissions
    
    # Organizational hierarchy
    manager: Optional[Link["EnhancedUser"]] = None
    direct_reports: List[Link["EnhancedUser"]] = Field(default_factory=list)
    
    # Context associations
    assigned_clients: List[Link[Client]] = Field(default_factory=list)  # Clients this user can access
    assigned_projects: List[Link[Project]] = Field(default_factory=list)  # Projects this user can access
    
    # Status
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[Link["EnhancedUser"]] = None
    
    class Settings:
        name = "enhanced_users"

class StakeholderIdentity(BaseModel):
    """Enhanced identity matching for stakeholders"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    linkedin_profile: Optional[str] = None
    alternate_identifiers: Dict[str, str] = Field(default_factory=dict)  # Custom identifiers
    
    def match_score(self, other: "StakeholderIdentity") -> float:
        """Calculate match score between two identities (0.0 to 1.0)"""
        score = 0.0
        total_weight = 0.0
        
        # Email match (highest weight)
        if self.email and other.email:
            total_weight += 0.4
            if self.email.lower() == other.email.lower():
                score += 0.4
        
        # Employee ID match (high weight)
        if self.employee_id and other.employee_id:
            total_weight += 0.3
            if self.employee_id == other.employee_id:
                score += 0.3
        
        # Phone match (medium weight)
        if self.phone and other.phone:
            total_weight += 0.2
            # Normalize phone numbers for comparison
            self_phone = ''.join(filter(str.isdigit, self.phone))
            other_phone = ''.join(filter(str.isdigit, other.phone))
            if self_phone == other_phone:
                score += 0.2
        
        # Name similarity (lower weight)
        total_weight += 0.1
        name_similarity = self._name_similarity(self.name, other.name)
        score += 0.1 * name_similarity
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity using simple token matching"""
        tokens1 = set(name1.lower().split())
        tokens2 = set(name2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)

class AccessControlList(Document):
    """Fine-grained access control for specific resources"""
    user: Link[EnhancedUser]
    resource_type: str  # "client", "project", "stakeholder", etc.
    resource_id: str    # ID of the specific resource
    permissions: List[Permission]
    granted_by: Link[EnhancedUser]
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Settings:
        name = "access_control_lists"

class AuditLog(Document):
    """Audit trail for all access control changes"""
    user: Link[EnhancedUser]
    action: str  # "create_user", "assign_role", "grant_permission", etc.
    target_user: Optional[Link[EnhancedUser]] = None
    target_resource: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Settings:
        name = "audit_logs"

# Default role definitions
DEFAULT_ROLES = [
    {
        "name": "Viewer",
        "access_level": AccessLevel.VIEWER,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.READ_STAKEHOLDERS
        ],
        "description": "Read-only access to assigned projects",
        "can_create_roles": [],
        "max_assignable_level": None
    },
    {
        "name": "Developer",
        "access_level": AccessLevel.CONTRIBUTOR,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS
        ],
        "description": "Can contribute to projects and update technical data",
        "can_create_roles": [],
        "max_assignable_level": None
    },
    {
        "name": "Team Lead",
        "access_level": AccessLevel.TEAM_LEAD,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS,
            Permission.READ_USERS,
            Permission.CREATE_USER
        ],
        "description": "Can manage team members and project data",
        "can_create_roles": [AccessLevel.VIEWER, AccessLevel.CONTRIBUTOR],
        "max_assignable_level": AccessLevel.CONTRIBUTOR
    },
    {
        "name": "Project Manager",
        "access_level": AccessLevel.PROJECT_MANAGER,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.WRITE_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.CREATE_PROJECT,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS,
            Permission.READ_USERS,
            Permission.CREATE_USER,
            Permission.MODIFY_USER
        ],
        "description": "Can manage projects and team assignments",
        "can_create_roles": [AccessLevel.VIEWER, AccessLevel.CONTRIBUTOR, AccessLevel.TEAM_LEAD],
        "max_assignable_level": AccessLevel.TEAM_LEAD
    },
    {
        "name": "Account Manager",
        "access_level": AccessLevel.ACCOUNT_MANAGER,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.WRITE_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.CREATE_PROJECT,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS,
            Permission.READ_FINANCIAL,
            Permission.WRITE_FINANCIAL,
            Permission.READ_USERS,
            Permission.CREATE_USER,
            Permission.MODIFY_USER
        ],
        "description": "Can manage client accounts and financial data",
        "can_create_roles": [AccessLevel.VIEWER, AccessLevel.CONTRIBUTOR, AccessLevel.TEAM_LEAD, AccessLevel.PROJECT_MANAGER],
        "max_assignable_level": AccessLevel.PROJECT_MANAGER
    },
    {
        "name": "Senior Manager",
        "access_level": AccessLevel.SENIOR_MANAGER,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.WRITE_CLIENT_DATA,
            Permission.DELETE_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.DELETE_PROJECT_DATA,
            Permission.CREATE_PROJECT,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS,
            Permission.DELETE_STAKEHOLDERS,
            Permission.READ_FINANCIAL,
            Permission.WRITE_FINANCIAL,
            Permission.READ_USERS,
            Permission.CREATE_USER,
            Permission.MODIFY_USER,
            Permission.ASSIGN_ROLES
        ],
        "description": "Can manage multiple accounts and assign roles",
        "can_create_roles": [AccessLevel.VIEWER, AccessLevel.CONTRIBUTOR, AccessLevel.TEAM_LEAD, 
                           AccessLevel.PROJECT_MANAGER, AccessLevel.ACCOUNT_MANAGER],
        "max_assignable_level": AccessLevel.ACCOUNT_MANAGER
    },
    {
        "name": "Head of Department",
        "access_level": AccessLevel.HOD,
        "permissions": [
            Permission.READ_CLIENT_DATA,
            Permission.WRITE_CLIENT_DATA,
            Permission.DELETE_CLIENT_DATA,
            Permission.READ_PROJECT_DATA,
            Permission.WRITE_PROJECT_DATA,
            Permission.DELETE_PROJECT_DATA,
            Permission.CREATE_PROJECT,
            Permission.READ_STAKEHOLDERS,
            Permission.WRITE_STAKEHOLDERS,
            Permission.DELETE_STAKEHOLDERS,
            Permission.READ_FINANCIAL,
            Permission.WRITE_FINANCIAL,
            Permission.READ_USERS,
            Permission.CREATE_USER,
            Permission.MODIFY_USER,
            Permission.DELETE_USER,
            Permission.ASSIGN_ROLES,
            Permission.AUDIT_LOGS
        ],
        "description": "Department head with full departmental access",
        "can_create_roles": [AccessLevel.VIEWER, AccessLevel.CONTRIBUTOR, AccessLevel.TEAM_LEAD, 
                           AccessLevel.PROJECT_MANAGER, AccessLevel.ACCOUNT_MANAGER, AccessLevel.SENIOR_MANAGER],
        "max_assignable_level": AccessLevel.SENIOR_MANAGER
    },
    {
        "name": "Executive",
        "access_level": AccessLevel.EXECUTIVE,
        "permissions": [perm for perm in Permission],  # All permissions
        "description": "C-level executive with full access",
        "can_create_roles": [level for level in AccessLevel if level != AccessLevel.ADMIN],
        "max_assignable_level": AccessLevel.HOD
    },
    {
        "name": "System Admin",
        "access_level": AccessLevel.ADMIN,
        "permissions": [perm for perm in Permission],  # All permissions
        "description": "System administrator with full system access",
        "can_create_roles": [level for level in AccessLevel],
        "max_assignable_level": AccessLevel.EXECUTIVE
    }
]