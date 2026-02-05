from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Shared Schemas ---

class TaskSchema(BaseModel):
    title: str
    status: str = "Upcoming"
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None

class InteractionSchema(BaseModel):
    title: str
    date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class TechItemSchema(BaseModel):
    name: str
    status: str = "Active"
    category: Optional[str] = None

class GoalSchema(BaseModel):
    goal: str
    timeline: Optional[str] = None
    priority: str = "Medium"

class StakeholderInfoSchema(BaseModel):
    name: str
    role: Optional[str] = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    sentiment: Optional[str] = "Neutral"
    influence: Optional[str] = "Medium"

class DocumentSourceSchema(BaseModel):
    source_type: str
    source_title: Optional[str] = None
    source_date: Optional[datetime] = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

# --- Section Read Schemas ---

class UniversalContextRead(BaseModel):
    id: str
    project_id: str
    summary: Optional[str] = None
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
    status_reason: Optional[str] = None
    tasks: List[TaskSchema] = []
    blockers: List[str] = []
    recent_interactions: List[InteractionSchema] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class TechnicalStateRead(BaseModel):
    id: str
    project_id: str
    tech_stack: List[TechItemSchema] = []
    credentials: List[Dict[str, str]] = []
    implementation_log: List[str] = []
    experiments: List[Dict[str, Any]] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class CommercialStateRead(BaseModel):
    id: str
    project_id: str
    active_sow: Dict[str, Any] = {}
    financials: Dict[str, Any] = {}
    invoicing_status: str
    renewals: List[Dict[str, Any]] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class StrategyStateRead(BaseModel):
    id: str
    project_id: str
    stakeholder_map: List[StakeholderInfoSchema] = []
    goals: List[GoalSchema] = []
    upsell_opportunities: List[Dict[str, Any]] = []
    competitors: List[Dict[str, Any]] = []
    platform_ecosystem: List[str] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class MarketingStateRead(BaseModel):
    id: str
    project_id: str
    brand_guidelines: Dict[str, Any] = {}
    success_stories: List[Dict[str, Any]] = []
    testimonials: List[Dict[str, Any]] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime

class MiscStateRead(BaseModel):
    id: str
    project_id: str
    feedback: List[Dict[str, Any]] = []
    subscriptions: List[Dict[str, Any]] = []
    reference_docs: List[Dict[str, Any]] = []
    additional_emails: List[str] = []
    sources: List[DocumentSourceSchema] = []
    last_updated: datetime
# --- Section Update Schemas (Optional Fields for PATCH) ---

class UniversalContextUpdate(BaseModel):
    summary: Optional[str] = None
    client_profile: Optional[Dict[str, Any]] = None
    squad: Optional[List[str]] = None
    pocs: Optional[List[StakeholderInfoSchema]] = None
    comm_hygiene: Optional[Dict[str, Any]] = None

class OperationsStateUpdate(BaseModel):
    overall_status: Optional[str] = None
    status_reason: Optional[str] = None
    tasks: Optional[List[TaskSchema]] = None
    blockers: Optional[List[str]] = None
    recent_interactions: Optional[List[InteractionSchema]] = None

class TechnicalStateUpdate(BaseModel):
    tech_stack: Optional[List[TechItemSchema]] = None
    credentials: Optional[List[Dict[str, str]]] = None
    implementation_log: Optional[List[str]] = None
    experiments: Optional[List[Dict[str, Any]]] = None

class CommercialStateUpdate(BaseModel):
    active_sow: Optional[Dict[str, Any]] = None
    financials: Optional[Dict[str, Any]] = None
    invoicing_status: Optional[str] = None
    renewals: Optional[List[Dict[str, Any]]] = None

class StrategyStateUpdate(BaseModel):
    stakeholder_map: Optional[List[StakeholderInfoSchema]] = None
    goals: Optional[List[GoalSchema]] = None
    upsell_opportunities: Optional[List[Dict[str, Any]]] = None
    competitors: Optional[List[Dict[str, Any]]] = None
    platform_ecosystem: Optional[List[str]] = None

class MarketingStateUpdate(BaseModel):
    brand_guidelines: Optional[Dict[str, Any]] = None
    success_stories: Optional[List[Dict[str, Any]]] = None
    testimonials: Optional[List[Dict[str, Any]]] = None

class MiscStateUpdate(BaseModel):
    feedback: Optional[List[Dict[str, Any]]] = None
    subscriptions: Optional[List[Dict[str, Any]]] = None
    reference_docs: Optional[List[Dict[str, Any]]] = None
    additional_emails: Optional[List[str]] = None
