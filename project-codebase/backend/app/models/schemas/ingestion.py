from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class IngestionRequest(BaseModel):
    source_type: str = Field(..., description="gmail | drive | manual | basecamp")
    text: str
    metadata: Optional[Dict[str, Any]] = {}
    client_id: Optional[str] = None
    project_id: Optional[str] = None
