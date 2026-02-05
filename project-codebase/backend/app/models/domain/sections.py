from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, date
from .base import Datapoint

# --- Nested Enums & Models ---

class HealthScore(BaseModel):
    value: Literal["Good", "At-Risk", "Poor"]
    reasoning: str

class POC(BaseModel):
    name: str
    role: str
    influence: Literal["Champion", "Supporter", "Neutral", "Blocker", "Unknown"] = "Unknown"
    email: Optional[str] = None
    last_contact: Optional[date] = None

class TimelineEvent(BaseModel):
    date: date
    event: str
    source_doc: Optional[str] = None

class Task(BaseModel):
    task_id: str
    name: str
    status: str
    owner: Optional[str] = None
    due_date: Optional[date] = None

class Blocker(BaseModel):
    issue: str
    severity: Literal["High", "Medium", "Low"]

class TechStackItem(BaseModel):
    name: str
    status: Literal["Active", "Planned", "Deprecated"]

class SOW(BaseModel):
    sow_id: Optional[str] = None
    contract_value: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Literal["Active", "Closed", "Pending"] = "Active"

class Invoice(BaseModel):
    invoice_number: str
    amount: float
    due_date: Optional[date] = None
    status: Literal["Paid", "Pending", "Overdue"]

class Stakeholder(BaseModel):
    name: str
    role: str
    influence_level: str
    sentiment: Literal["Champion", "Supporter", "Neutral", "Skeptic", "Blocker", "Unknown"]

# --- The 7 Sections ---

class UniversalContext(BaseModel):
    summary: Optional[Datapoint[str]] = None
    timeline: List[Datapoint[TimelineEvent]] = []
    engagement_type: Optional[Datapoint[str]] = None
    client_profile: Optional[Datapoint[dict]] = None # {name, industry, health_score...}
    squad: List[Datapoint[str]] = [] # Internal squad names
    poc_map: List[Datapoint[POC]] = []
    communication_hygiene: Optional[Datapoint[dict]] = None
    important_notes: List[Datapoint[str]] = []
    google_workspace: List[Datapoint[str]] = []

class Operations(BaseModel):
    traffic_light: Optional[Datapoint[Literal["Green", "Yellow", "Red"]]] = None
    task_board_upcoming: List[Datapoint[Task]] = []
    task_board_ongoing: List[Datapoint[Task]] = []
    blockers: List[Datapoint[Blocker]] = []
    recent_interactions: List[Datapoint[str]] = []
    engagement_status: Optional[Datapoint[str]] = None

class TechnicalIntelligence(BaseModel):
    tech_stack: List[Datapoint[TechStackItem]] = []
    access_credentials: List[Datapoint[dict]] = [] # Securely handled?
    implementation_log: List[Datapoint[str]] = []
    experiment_results: List[Datapoint[str]] = []

class Commercial(BaseModel):
    active_sow: Optional[Datapoint[SOW]] = None
    financial_overview: Optional[Datapoint[str]] = None
    invoices: List[Datapoint[Invoice]] = []
    upcoming_renewals: List[Datapoint[str]] = []
    revenue_channels: List[Datapoint[str]] = []

class Strategy(BaseModel):
    stakeholder_map: List[Datapoint[Stakeholder]] = []
    stakeholder_hierarchy: Optional[Datapoint[str]] = None # Tree representation?
    goals_roadmap: List[Datapoint[str]] = []
    upsell_opportunities: List[Datapoint[str]] = []
    competitors: List[Datapoint[str]] = []
    ecosystem: Optional[Datapoint[str]] = None

class Marketing(BaseModel):
    brand_guidelines: Optional[Datapoint[dict]] = None
    success_stories: List[Datapoint[str]] = None
    testimonials: List[Datapoint[str]] = None
    public_references: List[Datapoint[str]] = None

class Other(BaseModel):
    feedback: List[Datapoint[str]] = []
    subscriptions: List[Datapoint[str]] = []
    document_references: List[Datapoint[str]] = []
    additional_emails: List[Datapoint[str]] = []
