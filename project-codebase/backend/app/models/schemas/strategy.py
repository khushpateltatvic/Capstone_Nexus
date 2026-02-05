from typing import Optional, List, Dict, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Goal Schemas
class ClientGoalBase(BaseModel):
    goal: str
    priority: str
    timeline: Optional[str] = None

class ClientGoalCreate(ClientGoalBase):
    client_id: str
    stakeholder_id: Optional[str] = None

class ClientGoalRead(ClientGoalBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    stakeholder_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "stakeholder") and data.stakeholder:
            result["stakeholder_id"] = str(data.stakeholder.id) if hasattr(data.stakeholder, "id") else str(data.stakeholder)
        return result

# Upsell Schemas
class UpsellBase(BaseModel):
    title: str
    description: Optional[str] = None
    potential_value: Optional[float] = None
    probability: str = "Medium"
    status: str = "Identified"

class UpsellCreate(UpsellBase):
    client_id: str

class UpsellRead(UpsellBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result

# Competitor Schemas
class CompetitorBase(BaseModel):
    name: str
    strengths: List[str] = []
    weaknesses: List[str] = []
    threat_level: str = "Low"

class CompetitorCreate(CompetitorBase):
    client_id: str

class CompetitorRead(CompetitorBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result

# Platform Ecosystem
class PlatformBase(BaseModel):
    platform_name: str
    usage_status: str
    notes: Optional[str] = None

class PlatformCreate(PlatformBase):
    client_id: str

class PlatformRead(PlatformBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result
