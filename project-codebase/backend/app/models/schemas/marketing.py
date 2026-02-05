from typing import Optional, List, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Brand Guidelines
class BrandBase(BaseModel):
    brand_doc_link: str
    key_colors: Optional[List[str]] = None

class BrandCreate(BrandBase):
    client_id: str
    client_contact_email: Optional[str] = None

class BrandRead(BrandBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    client_contact_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client: 
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "client_contact") and data.client_contact:
            result["client_contact_id"] = str(data.client_contact.id) if hasattr(data.client_contact, "id") else str(data.client_contact)
        return result

# Success Story
class StoryBase(BaseModel):
    story: str
    approved: bool = False

class StoryCreate(StoryBase):
    client_id: str
    client_stakeholder_email: Optional[str] = None

class StoryRead(StoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    client_stakeholder_id: Optional[Union[PydanticObjectId, str]] = None
    created_by_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "client_stakeholder") and data.client_stakeholder:
            result["client_stakeholder_id"] = str(data.client_stakeholder.id) if hasattr(data.client_stakeholder, "id") else str(data.client_stakeholder)
        if hasattr(data, "created_by") and data.created_by:
            result["created_by_id"] = str(data.created_by.id) if hasattr(data.created_by, "id") else str(data.created_by)
        return result

# Testimonial
class TestimonialBase(BaseModel):
    quote: str
    approved: bool = False
    date: datetime = Field(default_factory=datetime.utcnow)

class TestimonialCreate(TestimonialBase):
    client_id: str
    stakeholder_id: str

class TestimonialRead(TestimonialBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    stakeholder_id: Union[PydanticObjectId, str]

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

# Public Reference
class ReferenceBase(BaseModel):
    title: str
    link: Optional[str] = None
    type: str # CaseStudy | Review | PressRelease
    date: datetime = Field(default_factory=datetime.utcnow)

class ReferenceCreate(ReferenceBase):
    client_id: str

class ReferenceRead(ReferenceBase):
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
