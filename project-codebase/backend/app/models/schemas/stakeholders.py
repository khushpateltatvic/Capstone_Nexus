from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ExternalStakeholderRead(BaseModel):
    id: str
    project_id: str
    name: str
    role: str
    category: str
    email: Optional[str] = None
    phone: Optional[str] = None
    sentiment: str
    influence: str
    last_updated: datetime

class ExternalStakeholderUpdate(BaseModel):
    role: Optional[str] = None
    category: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    sentiment: Optional[str] = None
    influence: Optional[str] = None
