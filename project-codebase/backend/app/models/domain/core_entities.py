from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import Document, Link, Indexed
from pydantic import Field
from bson import ObjectId

class Client(Document):
    name: Indexed(str, unique=True)  # Enforce unique client names
    industry: Optional[str] = None
    health_score: float = 100.0  # 0-100 logic (Good, Excellent, Bad mapped from float)
    engagement_start_date: Optional[datetime] = None
    engagement_type: str = "FTE" # FTE | Concierge | Other
    additional_emails: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "clients"

class Project(Document):
    client: Link[Client]  # Reference to Client document
    name: str
    status: str = "Active"
    news: List[Dict] = Field(default_factory=list) # [{title, url, source, date, relevance_score}]
    news_last_updated: Optional[datetime] = None
    intelligence: Dict[str, Any] = Field(default_factory=dict) # For AI modules (upsell, risk, knowledge)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "projects"
