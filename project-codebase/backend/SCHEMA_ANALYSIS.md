# Project Nexus - Schema & Endpoint Analysis

> **Generated:** February 5, 2026  
> **Purpose:** Analyze schema redundancy and document all models/endpoints in one place

---

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [User Schemas](#user-schemas)
3. [Client Schemas](#client-schemas)
4. [Project Schemas](#project-schemas)
5. [Section Schemas (7 Sections)](#section-schemas)
6. [Permission & RBAC Schemas](#permission--rbac-schemas)
7. [API Endpoints](#api-endpoints)
8. [Redundancy Analysis](#redundancy-analysis)

---

## Schema Overview

The project has schemas defined in **two locations**, leading to potential redundancy:

| Location | Purpose |
|----------|---------|
| `app/models/domain/` | Domain models (Beanie Documents, Pydantic BaseModels) |
| `app/models/schemas/` | API schemas (Create/Read/Update patterns) |

### Key Entities

| Entity | Domain File | Schema File |
|--------|-------------|-------------|
| User | `domain/user.py` | `schemas/auth.py` |
| Client | `domain/core_entities.py`, `domain/project.py` | Inline in endpoints |
| Project | `domain/project.py`, `domain/core_entities.py` | Inline in endpoints |
| Sections | `domain/sections.py` | `schemas/sections.py` + individual section files |
| Permissions | `domain/permissions.py` | - |

---

## User Schemas

### Domain: `app/models/domain/user.py`

```python
class UserRole(str, Enum):
    TRAINEE = "trainee"
    ANALYST = "analyst"
    LEAD = "lead"
    HEAD = "head"
    ADMIN = "admin"
    DIRECTOR = "director"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str]
    employee_number: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    role: UserRole = UserRole.TRAINEE
    manager_email: Optional[str]

class UserUpdate(BaseModel):
    full_name: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    role: Optional[UserRole]
    manager_email: Optional[str]
    is_active: Optional[bool]

class User(BaseModel):
    email: EmailStr
    hashed_password: str
    full_name: Optional[str]
    employee_number: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    role: UserRole = UserRole.TRAINEE
    reportees_count: int = 0
    manager_email: Optional[str]
    is_active: bool = True
    is_superuser: bool = False
    otp_code: Optional[str]
    otp_expires_at: Optional[datetime]
    created_at: datetime

class UserResponse(BaseModel):
    email: EmailStr
    full_name: Optional[str]
    employee_number: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    role: UserRole = UserRole.TRAINEE
    reportees_count: int = 0
    manager_email: Optional[str]
    is_active: bool = True
    is_superuser: bool = False
    permissions: List[str] = []

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

### Schema: `app/models/schemas/auth.py` ⚠️ DUPLICATE

```python
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):  # ❌ DUPLICATE of domain/user.py
    email: EmailStr
    password: str
    full_name: Optional[str]
    role: str = "Engineer"  # ⚠️ Different default!

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### 🔴 Redundancy Issue: `UserCreate` defined in BOTH files with different defaults!

---

## Client Schemas

### Domain: `app/models/domain/core_entities.py` (Beanie Document)

```python
class Client(Document):
    name: Indexed(str, unique=True)
    industry: Optional[str]
    health_score: float = 100.0
    engagement_start_date: Optional[datetime]
    engagement_type: str = "FTE"  # FTE | Concierge | Other
    additional_emails: List[str] = []
    created_at: datetime
    
    class Settings:
        name = "clients"
```

### Domain: `app/models/domain/project.py` (Pydantic - not Document)

```python
class Client(BaseModel):
    client_id: str
    name: str
    projects: List[Project] = []
    created_at: Optional[str]
    updated_at: Optional[str]
```

### Inline in `app/api/v1/endpoints/clients.py`

```python
class ClientCreate(BaseModel):
    client_id: str
    name: str
    industry: Optional[str]
    website: Optional[str]
    notes: Optional[str]

class ClientUpdate(BaseModel):
    name: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    notes: Optional[str]

class ClientResponse(BaseModel):
    client_id: str
    name: str
    industry: Optional[str]
    website: Optional[str]
    notes: Optional[str]
    project_count: int = 0
    created_at: Optional[str]
    updated_at: Optional[str]
```

### 🔴 Redundancy Issue: 
- **3 different Client definitions!**
- `core_entities.Client` uses Beanie Document with `name` as identifier
- `project.Client` uses Pydantic with `client_id` as identifier  
- Endpoint schemas use `client_id` consistently

---

## Project Schemas

### Domain: `app/models/domain/core_entities.py` (Beanie Document)

```python
class Project(Document):
    client: Link[Client]
    name: str
    status: str = "Active"
    news: List[Dict] = []
    news_last_updated: Optional[datetime]
    intelligence: Dict[str, Any] = {}
    created_at: datetime
    
    class Settings:
        name = "projects"
```

### Domain: `app/models/domain/project.py` (Pydantic - comprehensive)

```python
class ProjectAccess(BaseModel):
    assigned_users: List[str] = []
    delegated_permissions: List[Dict[str, Any]] = []
    section_overrides: Dict[str, Dict[str, str]] = {}
    sensitive_field_overrides: Dict[str, List[str]] = {}

class Project(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str]
    created_by: Optional[str]
    department: Optional[str]
    access: ProjectAccess = ProjectAccess()
    
    # The 7 Sections
    universal_context: UniversalContext
    operations: Operations
    technical: TechnicalIntelligence
    commercial: Commercial
    strategy: Strategy
    marketing: Marketing
    other: Other
    
    created_at: Optional[str]
    updated_at: Optional[str]
```

### Inline in `app/api/v1/endpoints/projects.py`

```python
class ProjectCreate(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str]
    department: Optional[str]
    assigned_users: List[str] = []

class ProjectUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    department: Optional[str]

class ProjectSummary(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str]
    department: Optional[str]
    created_by: Optional[str]
    sections_populated: List[str] = []
    assigned_users_count: int = 0
    created_at: Optional[str]
    updated_at: Optional[str]

class ProjectDetail(BaseModel):
    project_id: str
    client_id: str
    name: str
    description: Optional[str]
    department: Optional[str]
    created_by: Optional[str]
    access: Dict[str, Any] = {}
    universal_context: Dict[str, Any] = {}
    operations: Dict[str, Any] = {}
    technical: Dict[str, Any] = {}
    commercial: Dict[str, Any] = {}
    strategy: Dict[str, Any] = {}
    marketing: Dict[str, Any] = {}
    other: Dict[str, Any] = {}
    created_at: Optional[str]
    updated_at: Optional[str]
    user_permissions: Dict[str, str] = {}

class PermissionInfo(BaseModel):
    user_email: str
    role: Optional[str]
    job_title: Optional[str]
    type: str  # "assigned" or "delegated"
    sections: List[Dict[str, Any]] = []
    granted_by: Optional[str]
    status: Optional[str]
    expires_at: Optional[datetime]
```

### 🔴 Redundancy Issue:
- **2 different Project Document definitions!**
- `core_entities.Project` uses Link[Client] and minimal fields
- `domain/project.Project` has full section structure but is Pydantic (not persisted directly)
- Endpoint schemas duplicate basic fields again

---

## Section Schemas

### The 7 Project Sections

| # | Section | Domain Location | Schema Location |
|---|---------|-----------------|-----------------|
| 1 | Universal Context | `domain/sections.py` | `schemas/sections.py`, `schemas/universal_context.py` |
| 2 | Operations | `domain/sections.py` | `schemas/sections.py`, `schemas/operations.py` |
| 3 | Technical Intelligence | `domain/sections.py` | `schemas/sections.py`, `schemas/technical.py` |
| 4 | Commercial | `domain/sections.py` | `schemas/sections.py`, `schemas/commercial.py` |
| 5 | Strategy | `domain/sections.py` | `schemas/sections.py`, `schemas/strategy.py` |
| 6 | Marketing | `domain/sections.py` | `schemas/sections.py`, `schemas/marketing.py` |
| 7 | Other/Misc | `domain/sections.py` | `schemas/sections.py`, `schemas/misc.py` |

### Domain: `app/models/domain/sections.py` (with Datapoint wrapper)

```python
# --- Nested Types ---
class HealthScore(BaseModel):
    value: Literal["Good", "At-Risk", "Poor"]
    reasoning: str

class POC(BaseModel):
    name: str
    role: str
    influence: Literal["Champion", "Supporter", "Neutral", "Blocker", "Unknown"]
    email: Optional[str]
    last_contact: Optional[date]

class TimelineEvent(BaseModel):
    date: date
    event: str
    source_doc: Optional[str]

class Task(BaseModel):
    task_id: str
    name: str
    status: str
    owner: Optional[str]
    due_date: Optional[date]

class Blocker(BaseModel):
    issue: str
    severity: Literal["High", "Medium", "Low"]

class TechStackItem(BaseModel):
    name: str
    status: Literal["Active", "Planned", "Deprecated"]

class SOW(BaseModel):
    sow_id: Optional[str]
    contract_value: Optional[float]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Literal["Active", "Closed", "Pending"]

class Invoice(BaseModel):
    invoice_number: str
    amount: float
    due_date: Optional[date]
    status: Literal["Paid", "Pending", "Overdue"]

class Stakeholder(BaseModel):
    name: str
    role: str
    influence_level: str
    sentiment: Literal["Champion", "Supporter", "Neutral", "Skeptic", "Blocker", "Unknown"]

# --- The 7 Sections (all using Datapoint[T] wrapper) ---
class UniversalContext(BaseModel):
    summary: Optional[Datapoint[str]]
    timeline: List[Datapoint[TimelineEvent]] = []
    engagement_type: Optional[Datapoint[str]]
    client_profile: Optional[Datapoint[dict]]
    squad: List[Datapoint[str]] = []
    poc_map: List[Datapoint[POC]] = []
    communication_hygiene: Optional[Datapoint[dict]]
    important_notes: List[Datapoint[str]] = []
    google_workspace: List[Datapoint[str]] = []

class Operations(BaseModel):
    traffic_light: Optional[Datapoint[Literal["Green", "Yellow", "Red"]]]
    task_board_upcoming: List[Datapoint[Task]] = []
    task_board_ongoing: List[Datapoint[Task]] = []
    blockers: List[Datapoint[Blocker]] = []
    recent_interactions: List[Datapoint[str]] = []
    engagement_status: Optional[Datapoint[str]]

class TechnicalIntelligence(BaseModel):
    tech_stack: List[Datapoint[TechStackItem]] = []
    access_credentials: List[Datapoint[dict]] = []
    implementation_log: List[Datapoint[str]] = []
    experiment_results: List[Datapoint[str]] = []

class Commercial(BaseModel):
    active_sow: Optional[Datapoint[SOW]]
    financial_overview: Optional[Datapoint[str]]
    invoices: List[Datapoint[Invoice]] = []
    upcoming_renewals: List[Datapoint[str]] = []
    revenue_channels: List[Datapoint[str]] = []

class Strategy(BaseModel):
    stakeholder_map: List[Datapoint[Stakeholder]] = []
    stakeholder_hierarchy: Optional[Datapoint[str]]
    goals_roadmap: List[Datapoint[str]] = []
    upsell_opportunities: List[Datapoint[str]] = []
    competitors: List[Datapoint[str]] = []
    ecosystem: Optional[Datapoint[str]]

class Marketing(BaseModel):
    brand_guidelines: Optional[Datapoint[dict]]
    success_stories: List[Datapoint[str]] = None  # ⚠️ Should be []
    testimonials: List[Datapoint[str]] = None     # ⚠️ Should be []
    public_references: List[Datapoint[str]] = None # ⚠️ Should be []

class Other(BaseModel):
    feedback: List[Datapoint[str]] = []
    subscriptions: List[Datapoint[str]] = []
    document_references: List[Datapoint[str]] = []
    additional_emails: List[Datapoint[str]] = []
```

### Schema: `app/models/schemas/sections.py` (API schemas - NO Datapoint wrapper)

```python
# --- Shared Schemas ---
class TaskSchema(BaseModel):
    title: str
    status: str = "Upcoming"
    due_date: Optional[datetime]
    assigned_to: Optional[str]

class InteractionSchema(BaseModel):
    title: str
    date: datetime
    notes: Optional[str]

class TechItemSchema(BaseModel):
    name: str
    status: str = "Active"
    category: Optional[str]

class GoalSchema(BaseModel):
    goal: str
    timeline: Optional[str]
    priority: str = "Medium"

class StakeholderInfoSchema(BaseModel):
    name: str
    role: Optional[str] = "Unknown"
    email: Optional[str]
    phone: Optional[str]
    sentiment: Optional[str] = "Neutral"
    influence: Optional[str] = "Medium"

class DocumentSourceSchema(BaseModel):
    source_type: str
    source_title: Optional[str]
    source_date: Optional[datetime]
    extracted_at: datetime

# --- Section Read Schemas ---
class UniversalContextRead(BaseModel):
    id: str
    project_id: str
    summary: Optional[str]
    client_profile: Dict[str, Any] = {}
    squad: List[str] = []
    pocs: List[StakeholderInfoSchema] = []
    comm_hygiene: Dict[str, Any] = {}
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class OperationsStateRead(BaseModel):
    id: str
    project_id: str
    overall_status: str
    status_reason: Optional[str]
    tasks: List[TaskSchema] = []
    blockers: List[str] = []
    recent_interactions: List[InteractionSchema] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

# ... (similar for other sections)

# --- Section Update Schemas ---
class UniversalContextUpdate(BaseModel):
    summary: Optional[str]
    client_profile: Optional[Dict[str, Any]]
    squad: Optional[List[str]]
    pocs: Optional[List[StakeholderInfoSchema]]
    comm_hygiene: Optional[Dict[str, Any]]

class OperationsStateUpdate(BaseModel):
    overall_status: Optional[str]
    status_reason: Optional[str]
    tasks: Optional[List[TaskSchema]]
    blockers: Optional[List[str]]
    recent_interactions: Optional[List[InteractionSchema]]

# ... (similar for other sections)
```

### Individual Section Schema Files (MORE duplication!)

Each section has its own schema file with Beanie-style Create/Read patterns:

#### `schemas/operations.py`
```python
class TaskBase(BaseModel):
    title: str
    status: str  # Upcoming | Done | InProgress
    due_date: Optional[datetime]
    is_blocker: bool = False
    blocker_description: Optional[str]

class TaskCreate(TaskBase):
    project_id: str
    assigned_to_email: Optional[str]
    requested_by_email: Optional[str]

class TaskRead(TaskBase):
    id: Union[PydanticObjectId, str]
    project_id: Union[PydanticObjectId, str]
    assigned_to_id: Optional[Union[PydanticObjectId, str]]
    # + model_validator for link extraction
```

#### `schemas/commercial.py`
```python
class ActiveSOWBase(BaseModel):
    scope_summary: str
    start_date: date
    end_date: date
    value: Optional[float]
    billing_model: Optional[str] = "Fixed"

class ActiveSOWCreate(ActiveSOWBase):
    client_id: str
    client_contact_email: Optional[str]
    account_manager_email: Optional[str]

class ActiveSOWRead(ActiveSOWBase):
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    # + model_validator
```

### 🔴 Redundancy Issue:
- **TRIPLE definition** of section structures:
  1. `domain/sections.py` - with Datapoint wrapper
  2. `schemas/sections.py` - API Read/Update schemas
  3. Individual `schemas/*.py` files - Beanie-style CRUD schemas
- Field naming inconsistencies (e.g., `task_board_upcoming` vs `tasks`)
- Some use Beanie Links, some use plain IDs

---

## Permission & RBAC Schemas

### Domain: `app/models/domain/permissions.py`

```python
class PermissionLevel(str, Enum):
    NONE = "none"
    VIEW = "view"
    EDIT = "edit"
    FULL = "full"

class SectionPermission(BaseModel):
    section: str
    level: PermissionLevel = PermissionLevel.VIEW
    fields_hidden: List[str] = []

class DelegatedPermission(BaseModel):
    user_email: str
    granted_by: str
    sections: List[SectionPermission] = []
    expires_at: Optional[datetime]
    status: str = "active"
    created_at: datetime
    approved_at: Optional[datetime]
    notes: Optional[str]

class DelegatePermissionRequest(BaseModel):
    user_email: str
    sections: List[SectionPermission]
    expires_at: Optional[datetime]
    requires_approval: bool = False
    notes: Optional[str]

class AssignUserRequest(BaseModel):
    user_email: str
    sections: Optional[List[SectionPermission]]

class UpdatePermissionRequest(BaseModel):
    sections: List[SectionPermission]
    expires_at: Optional[datetime]

# Default section access by role
DEFAULT_SECTION_ACCESS: Dict[str, Dict[str, PermissionLevel]] = {
    "universal_context": {...},
    "operations": {...},
    # ...
}

SENSITIVE_FIELDS: Dict[str, List[str]] = {
    "stakeholder_map": ["lead", "head", "admin", "director"],
    "financial_overview": ["head", "admin", "director"],
    # ...
}
```

### Domain: `app/models/domain/base.py`

```python
class Datapoint(BaseModel, Generic[T]):
    """Wrapper for any data point to provide lineage and confidence."""
    value: Optional[T]
    source_doc_id: Optional[str]
    confidence: float  # 0.0-1.0
    reasoning: Optional[str]
    last_updated: datetime

class AgentOutput(BaseModel):
    """Base class for agent returns."""
    agent_name: str
    processed_at: datetime
```

---

## API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login/access-token` | OAuth2 token generation |
| POST | `/register` | Register user (admin secret required) |
| GET | `/me` | Get current user profile |
| PUT | `/me` | Update current user profile |
| POST | `/change-password` | Change password |
| POST | `/forgot-password` | Request password reset OTP |
| POST | `/reset-password` | Reset password with OTP |
| GET | `/users` | List all users (admin only) |
| GET | `/users/{email}` | Get user by email |
| PUT | `/users/{email}` | Update user (admin only) |

### Clients (`/api/v1/clients`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all accessible clients |
| GET | `/{client_id}` | Get client details |
| POST | `/` | Create new client |
| PUT | `/{client_id}` | Update client |
| DELETE | `/{client_id}` | Delete client |

### Projects (`/api/v1/projects`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all accessible projects |
| GET | `/{client_id}` | List client's projects |
| GET | `/{client_id}/{project_id}` | Get project details |
| POST | `/` | Create project (admin only) |
| PUT | `/{client_id}/{project_id}` | Update project (admin only) |
| DELETE | `/{client_id}/{project_id}` | Delete project (admin only) |
| GET | `/{client_id}/{project_id}/permissions` | List permissions |
| POST | `/{client_id}/{project_id}/permissions/assign` | Assign user |
| POST | `/{client_id}/{project_id}/permissions/delegate` | Delegate to junior |
| PUT | `/{client_id}/{project_id}/permissions/{email}` | Update permissions |
| DELETE | `/{client_id}/{project_id}/permissions/{email}` | Remove access |
| POST | `/{client_id}/{project_id}/permissions/approve/{email}` | Approve pending |
| POST | `/{client_id}/{project_id}/news/refresh` | Refresh project news |
| GET | `/{client_id}/{project_id}/news` | Get project news |

### Sections (`/api/v1/sections`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}/{section_name}` | Get section data |
| PUT | `/{client_id}/{project_id}/{section_name}` | Replace section |
| PATCH | `/{client_id}/{project_id}/{section_name}` | Partial update section |
| DELETE | `/{client_id}/{project_id}/{section_name}` | Clear section |
| GET | `/{client_id}/{project_id}/{section_name}/{field_name}` | Get specific field |
| PUT | `/{client_id}/{project_id}/{section_name}/{field_name}` | Update specific field |
| DELETE | `/{client_id}/{project_id}/{section_name}/{field_name}` | Delete specific field |
| GET | `/{client_id}/{project_id}/{section_name}/permissions` | Get section permissions |
| PUT | `/{client_id}/{project_id}/{section_name}/permissions` | Update section permissions |

### Universal Context (`/api/v1/universal-context`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/squad-search-users` | Get all users for squad search |
| GET | `/{client_id}/{project_id}` | Get universal context |
| PUT | `/{client_id}/{project_id}` | Update universal context |
| GET/PUT | `/{client_id}/{project_id}/summary` | Summary field |
| GET/PUT | `/{client_id}/{project_id}/timeline` | Timeline field |
| POST | `/{client_id}/{project_id}/timeline` | Add timeline event |
| GET/PUT | `/{client_id}/{project_id}/engagement_type` | Engagement type |
| GET/PUT | `/{client_id}/{project_id}/client_profile` | Client profile |
| GET/PUT | `/{client_id}/{project_id}/squad` | Internal squad |
| POST | `/{client_id}/{project_id}/squad` | Add squad member |
| GET/PUT/POST | `/{client_id}/{project_id}/pocs` | POC contacts |
| GET/PUT | `/{client_id}/{project_id}/comm_hygiene` | Communication hygiene |
| GET/PUT/POST | `/{client_id}/{project_id}/notes` | Important notes |
| GET/PUT | `/{client_id}/{project_id}/workspace` | Google workspace |

### Operations (`/api/v1/operations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get operations data |
| PUT | `/{client_id}/{project_id}` | Update operations |
| GET/PUT | `/{client_id}/{project_id}/traffic_light` | Traffic light status |
| GET | `/{client_id}/{project_id}/tasks` | Get all tasks |
| PUT/POST | `/{client_id}/{project_id}/tasks/upcoming` | Upcoming tasks |
| PUT/POST | `/{client_id}/{project_id}/tasks/ongoing` | Ongoing tasks |
| GET/PUT/POST | `/{client_id}/{project_id}/blockers` | Blockers |
| GET/PUT/POST | `/{client_id}/{project_id}/interactions` | Recent interactions |

### Technical (`/api/v1/technical`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get technical data |
| PUT | `/{client_id}/{project_id}` | Update technical |
| GET/PUT/POST | `/{client_id}/{project_id}/tech_stack` | Tech stack |
| GET/PUT/POST | `/{client_id}/{project_id}/credentials` | Access credentials |
| GET/PUT/POST | `/{client_id}/{project_id}/implementations` | Implementation log |
| GET/PUT/POST | `/{client_id}/{project_id}/experiments` | Experiments |

### Commercial (`/api/v1/commercial`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get commercial data |
| PUT | `/{client_id}/{project_id}` | Update commercial |
| GET/PUT | `/{client_id}/{project_id}/sow` | Active SOW |
| GET/PUT | `/{client_id}/{project_id}/financial` | Financial overview |
| GET/PUT/POST | `/{client_id}/{project_id}/invoices` | Invoices |
| GET/PUT/POST | `/{client_id}/{project_id}/renewals` | Renewals |
| GET/PUT | `/{client_id}/{project_id}/revenue_channels` | Revenue channels |

### Strategy (`/api/v1/strategy`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get strategy data |
| PUT | `/{client_id}/{project_id}` | Update strategy |
| GET/PUT/POST | `/{client_id}/{project_id}/stakeholders` | Stakeholder map |
| GET/PUT/POST | `/{client_id}/{project_id}/goals` | Goals roadmap |
| GET/PUT/POST | `/{client_id}/{project_id}/upsells` | Upsell opportunities |
| GET/PUT/POST | `/{client_id}/{project_id}/competitors` | Competitors |
| GET/PUT | `/{client_id}/{project_id}/ecosystem` | Platform ecosystem |

### Marketing (`/api/v1/marketing`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get marketing data |
| PUT | `/{client_id}/{project_id}` | Update marketing |
| GET/PUT | `/{client_id}/{project_id}/brand` | Brand guidelines |
| GET/PUT | `/{client_id}/{project_id}/success_stories` | Success stories |
| GET/PUT | `/{client_id}/{project_id}/testimonials` | Testimonials |
| GET/PUT | `/{client_id}/{project_id}/references` | Public references |
| POST | `/{client_id}/{project_id}/generate` | Generate marketing content |

### Other/Misc (`/api/v1/other`, `/api/v1/misc`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/{project_id}` | Get other data |
| PUT | `/{client_id}/{project_id}` | Update other |
| GET/PUT/POST | `/{client_id}/{project_id}/notes` | Key notes |
| GET/PUT | `/{client_id}/{project_id}/custom/{field_name}` | Custom fields |
| GET | `/{project_id}` (misc) | Get misc state |
| PATCH | `/{project_id}` (misc) | Partial update misc |
| DELETE | `/{project_id}` (misc) | Delete misc |

### Dashboard (`/api/v1/dashboard`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{client_id}/dashboard` | Get client dashboard |
| GET | `/{client_id}/operations` | Get aggregated operations |

### Chat (`/api/v1/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ask` | Ask Nexus AI |

### Automation (`/api/v1/automation`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync` | Trigger manual sync |
| POST | `/basecamp/sync` | Sync all Basecamp projects |
| POST | `/basecamp/sync/{project_id}` | Sync specific project |
| GET | `/basecamp/status` | Get Basecamp status |
| POST | `/basecamp/reset` | Reset sync state |
| POST | `/ingest` | Ingest document to vector store |
| POST | `/ingest-batch` | Batch ingest documents |
| POST | `/extract` | RAG extraction |
| POST | `/process` | Combined ingest + extract |
| DELETE | `/clear/{client_id}/{project_id}` | Clear project vectors |
| GET | `/startup/status` | Get startup automation status |
| POST | `/startup/check` | Trigger startup check |

### Admin (`/api/v1/admin`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List users for assignment |
| GET | `/roles` | List active roles |
| GET | `/projects/{project_id}/team` | Get project team |
| POST | `/projects/{project_id}/assign` | Assign user to project |

### Access Control (`/api/v1/access`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/stakeholders/internal` | Create internal stakeholder |
| PUT | `/stakeholders/access` | Update stakeholder access |
| POST | `/projects/{project_id}/manual-assignment` | Manual assignment |
| GET | `/my-permissions` | Get current user permissions |
| GET | `/projects` | List accessible projects |
| GET | `/clients` | List accessible clients |
| GET | `/stakeholders` | List stakeholders |
| POST | `/access-rules` | Create access rules |
| GET | `/projects/{project_id}/available-members` | Available team members |
| GET | `/hierarchy` | Get organization hierarchy |

### Intelligence Services

| Router | Endpoint | Description |
|--------|----------|-------------|
| `/api/v1/knowledge` | `/{project_id}/matches` | Knowledge bridge matches |
| `/api/v1/upsell` | `/{project_id}/generate` | Generate upsell opportunities |
| `/api/v1/upsell` | `/{project_id}` | Get stored upsells |
| `/api/v1/risk` | `/{project_id}/analyze` | Analyze project risk |
| `/api/v1/risk` | `/{project_id}` | Get stored risk analysis |
| `/api/v1/stakeholders` | `/{project_id}` | List external stakeholders |
| `/api/v1/stakeholders` | `/{stakeholder_id}` | Update/Delete stakeholder |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/projects/{project_id}` | HTML project report |
| GET | `/api/v1/reports-enhanced/projects/{project_id}` | Enhanced HTML report |

### Ingestion

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingestion/upload` | Upload text for ingestion |
| POST | `/api/v1/ingest/manual` | Manual file upload |
| GET | `/api/v1/ingest/status` | Get ingest queue status |

---

## Redundancy Analysis

### 🔴 Critical Issues

1. **User Schema Duplication**
   - `domain/user.py::UserCreate` vs `schemas/auth.py::UserCreate`
   - Different default roles!

2. **Client Model Confusion**
   - 3 different definitions across files
   - Beanie Document vs Pydantic BaseModel
   - Inconsistent identifier (`name` vs `client_id`)

3. **Project Model Duplication**
   - Beanie `core_entities.Project` (minimal)
   - Pydantic `domain/project.Project` (comprehensive)
   - Neither used consistently in endpoints

4. **Section Schema Explosion**
   - Domain sections with Datapoint[T] wrapper
   - API schemas without wrapper
   - Individual CRUD schemas per section
   - **3x redundancy for each section!**

### 🟡 Moderate Issues

1. **Inconsistent Field Naming**
   - `task_board_upcoming` vs `tasks`
   - `poc_map` vs `pocs`
   - `traffic_light` types differ

2. **Mixed ORM Patterns**
   - Some use Beanie Documents
   - Some use raw MongoDB operations
   - Some use plain Pydantic

3. **Endpoint-Defined Schemas**
   - Many request/response models defined inline
   - Should be in dedicated schema files

### 🟢 Recommendations

1. **Consolidate User Schemas** → Single source in `domain/user.py`
2. **Pick One Client/Project Model** → Use Pydantic with `client_id/project_id`
3. **Eliminate Section Schema Duplication**:
   - Keep `domain/sections.py` for internal use with Datapoint
   - Keep `schemas/sections.py` for API
   - Remove individual section schema files
4. **Standardize Field Names** across all layers
5. **Move Inline Schemas** to dedicated files
6. **Document Data Flow** → Which schema is used where

---

## File Reference

### Domain Models (`app/models/domain/`)
- `base.py` - Datapoint, AgentOutput
- `user.py` - User, UserCreate, UserUpdate, UserResponse
- `project.py` - Project, Client, ProjectAccess
- `core_entities.py` - Beanie Client, Project Documents
- `sections.py` - 7 section models with Datapoint wrapper
- `permissions.py` - RBAC models
- `document_references.py` - DocumentSource, Stakeholders, Assignments
- `access_control.py`, `rbac.py` - Additional access control

### API Schemas (`app/models/schemas/`)
- `auth.py` - Token, UserCreate (duplicate!), UserLogin
- `sections.py` - Section Read/Update schemas
- `universal_context.py` - AccountSummary schemas
- `operations.py` - Escalation, Task, Interaction schemas
- `commercial.py` - SOW, Renewal, Financial schemas
- `technical.py` - TechStack, Credential, Experiment schemas
- `strategy.py` - Goal, Upsell, Competitor, Platform schemas
- `marketing.py` - Brand, Story, Testimonial, Reference schemas
- `misc.py` - Feedback, Subscription, Note, DocRef schemas
- `stakeholders.py` - ExternalStakeholder schemas
- `ingestion.py` - IngestionRequest

### Chat Schema (`app/schemas/`)
- `chat.py` - ChatRequest, ChatResponse
