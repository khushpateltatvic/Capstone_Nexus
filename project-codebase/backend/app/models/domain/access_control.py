from typing import List, Dict, Optional
from beanie import Document
from pydantic import Field, BaseModel
from datetime import datetime

class RolePermission(Document):
    """
    Stores the access matrix for a specific Role + Department combo.
    Defines View (V), Edit (E), Hide (H) permissions for each data point.
    """
    role: str
    department: str
    
    # Permission Matrix: key = section_id (or refined key), value = "V" | "E" | "H"
    # We will map the 23 points from the excel to granular keys
    permissions: Dict[str, str] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "role_permissions"
        indexes = [
            [("role", 1), ("department", 1)],  # Unique compound index logic handled in app
        ]

class AccessRequest(BaseModel):
    user_id: str
    resource_type: str # 'universal_context', 'financials', etc
    action: str # 'read', 'write'
