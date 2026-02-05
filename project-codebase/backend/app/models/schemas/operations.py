from typing import Optional, List, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Escalation Schemas
class EscalationBase(BaseModel):
    status: str # Red | Amber | Green
    reason: str

class EscalationCreate(EscalationBase):
    client_id: str
    reported_by_email: Optional[str] = None
    client_contact_email: Optional[str] = None

class EscalationRead(EscalationBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    last_updated: datetime
    reported_by_id: Optional[Union[PydanticObjectId, str]] = None
    client_contact_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "reported_by") and data.reported_by:
            result["reported_by_id"] = str(data.reported_by.id) if hasattr(data.reported_by, "id") else str(data.reported_by)
        if hasattr(data, "client_contact") and data.client_contact:
            result["client_contact_id"] = str(data.client_contact.id) if hasattr(data.client_contact, "id") else str(data.client_contact)
        return result

# Task Schemas
class TaskBase(BaseModel):
    title: str
    status: str # Upcoming | Done | InProgress
    due_date: Optional[datetime] = None
    is_blocker: bool = False
    blocker_description: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: str
    assigned_to_email: Optional[str] = None
    requested_by_email: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    is_blocker: Optional[bool] = None
    blocker_description: Optional[str] = None
    assigned_to_email: Optional[str] = None

class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    project_id: Union[PydanticObjectId, str]
    assigned_to_id: Optional[Union[PydanticObjectId, str]] = None
    requested_by_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "project") and data.project:
            result["project_id"] = str(data.project.id) if hasattr(data.project, "id") else str(data.project)
        if hasattr(data, "assigned_to") and data.assigned_to:
            result["assigned_to_id"] = str(data.assigned_to.id) if hasattr(data.assigned_to, "id") else str(data.assigned_to)
        if hasattr(data, "requested_by") and data.requested_by:
            result["requested_by_id"] = str(data.requested_by.id) if hasattr(data.requested_by, "id") else str(data.requested_by)
        return result

# Interaction Schemas
class InteractionBase(BaseModel):
    type: str # Meeting | Email | Call | Slack
    title: str
    description: Optional[str] = None
    date: datetime = Field(default_factory=datetime.utcnow)
    sentiment: str = "Neutral"
    action_items: List[str] = []

class InteractionCreate(InteractionBase):
    client_id: str
    project_id: Optional[str] = None
    internal_attendee_emails: List[str] = []
    client_attendee_emails: List[str] = []

class InteractionRead(InteractionBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    project_id: Optional[Union[PydanticObjectId, str]] = None
    internal_attendee_ids: List[Union[PydanticObjectId, str]] = []
    client_attendee_ids: List[Union[PydanticObjectId, str]] = []

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "project") and data.project:
            result["project_id"] = str(data.project.id) if hasattr(data.project, "id") else str(data.project)
        
        if hasattr(data, "internal_attendees") and data.internal_attendees:
            result["internal_attendee_ids"] = [str(a.id) if hasattr(a, "id") else str(a) for a in data.internal_attendees]
        if hasattr(data, "client_attendees") and data.client_attendees:
            result["client_attendee_ids"] = [str(a.id) if hasattr(a, "id") else str(a) for a in data.client_attendees]
        return result
