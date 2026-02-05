from typing import Optional, List, Dict, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

class AccountSummaryBase(BaseModel):
    summary: str
    timeline: List[Dict[str, Any]] = []
    industry_context: Optional[str] = None
    engagement_overview: Optional[str] = None
    last_email: Optional[datetime] = None
    last_meeting: Optional[datetime] = None
    response_time_avg: Optional[float] = None
    meeting_frequency: Optional[str] = None
    important_notes: Optional[str] = None
    google_workspace_team: Optional[str] = None

class AccountSummaryCreate(AccountSummaryBase):
    client_id: str
    account_id: str

class AccountSummaryUpdate(BaseModel):
    summary: Optional[str] = None
    timeline: Optional[List[Dict[str, Any]]] = None
    industry_context: Optional[str] = None
    engagement_overview: Optional[str] = None
    last_email: Optional[datetime] = None
    last_meeting: Optional[datetime] = None
    response_time_avg: Optional[float] = None
    meeting_frequency: Optional[str] = None
    important_notes: Optional[str] = None
    google_workspace_team: Optional[str] = None

class AccountSummaryRead(AccountSummaryBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    account_id: str
    last_updated: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {}
        for field in cls.model_fields:
            if hasattr(data, field):
                result[field] = getattr(data, field)
        
        # Explicitly handle IDs and Links as strings for maximum compatibility
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            link = getattr(data, "client")
            result["client_id"] = str(link.id) if hasattr(link, "id") else str(link)
            
        return result
