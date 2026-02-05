from typing import Optional, List, Dict, Any, Union
from beanie import PydanticObjectId
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

# Tech Stack Schemas
class TechStackBase(BaseModel):
    technology: str
    category: Optional[str] = None
    status: str = "Active"

class TechStackCreate(TechStackBase):
    project_id: str
    implemented_by_email: Optional[str] = None

class TechStackRead(TechStackBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    project_id: Union[PydanticObjectId, str]
    updated_at: datetime
    implemented_by_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "project") and data.project:
            result["project_id"] = str(data.project.id) if hasattr(data.project, "id") else str(data.project)
        if hasattr(data, "implemented_by") and data.implemented_by:
            result["implemented_by_id"] = str(data.implemented_by.id) if hasattr(data.implemented_by, "id") else str(data.implemented_by)
        return result

# Access Credentials
class AccessCredentialBase(BaseModel):
    system_name: str
    environment: str
    access_type: str
    details: str

class AccessCredentialCreate(AccessCredentialBase):
    project_id: str

class AccessCredentialRead(AccessCredentialBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    project_id: Union[PydanticObjectId, str]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "project") and data.project:
            result["project_id"] = str(data.project.id) if hasattr(data.project, "id") else str(data.project)
        return result

# Experiment Results
class ExperimentBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str
    outcome: Optional[str] = None
    metrics: Dict[str, Any] = {}

class ExperimentCreate(ExperimentBase):
    project_id: str

class ExperimentRead(ExperimentBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    project_id: Union[PydanticObjectId, str]
    date: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "project") and data.project:
            result["project_id"] = str(data.project.id) if hasattr(data.project, "id") else str(data.project)
        return result
