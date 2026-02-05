from typing import Optional, List, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Feedback Schemas
class FeedbackBase(BaseModel):
    raw_feedback: str
    rephrased_feedback: Optional[str] = None
    sentiment: str

class FeedbackCreate(FeedbackBase):
    client_id: str
    provided_by_email: Optional[str] = None

class FeedbackRead(FeedbackBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    provided_by_id: Optional[Union[PydanticObjectId, str]] = None
    recorded_by_id: Optional[Union[PydanticObjectId, str]] = None
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "provided_by") and data.provided_by:
            result["provided_by_id"] = str(data.provided_by.id) if hasattr(data.provided_by, "id") else str(data.provided_by)
        if hasattr(data, "recorded_by") and data.recorded_by:
            result["recorded_by_id"] = str(data.recorded_by.id) if hasattr(data.recorded_by, "id") else str(data.recorded_by)
        return result

# Subscription Schemas
class SubscriptionBase(BaseModel):
    key_goal: str
    status: str

class SubscriptionCreate(SubscriptionBase):
    client_id: str

class SubscriptionRead(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result

# Key Notes
class NoteBase(BaseModel):
    note: str
    visibility: str = "team"

class NoteCreate(NoteBase):
    client_id: str

class NoteRead(NoteBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    created_by_id: Union[PydanticObjectId, str]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "created_by") and data.created_by:
            result["created_by_id"] = str(data.created_by.id) if hasattr(data.created_by, "id") else str(data.created_by)
        return result

# Document Reference Schemas
class DocRefBase(BaseModel):
    source_type: str
    source_id: str
    source_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    sensitivity_level: str = "internal"

class DocRefCreate(DocRefBase):
    client_id: Optional[str] = None
    project_id: Optional[str] = None
    internal_stakeholder_emails: List[str] = []

class DocRefRead(DocRefBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Optional[Union[PydanticObjectId, str]] = None
    project_id: Optional[Union[PydanticObjectId, str]] = None
    created_date: Optional[datetime] = None
    last_accessed: datetime

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
        return result
