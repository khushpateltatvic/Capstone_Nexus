from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")

class Datapoint(BaseModel, Generic[T]):
    """
    Wrapper for any data point to provide lineage and confidence.
    """
    value: Optional[T] = None
    source_doc_id: Optional[str] = Field(None, description="ID of the document this was extracted from")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of extraction")
    reasoning: Optional[str] = Field(None, description="LLM reasoning for this value")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AgentOutput(BaseModel):
    """Base class for what an agent returns before reducing."""
    agent_name: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
