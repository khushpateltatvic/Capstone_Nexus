from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    client_id: Optional[str] = None  # Filter chat to specific client
    project_id: Optional[str] = None  # Filter chat to specific project
    history: Optional[List[dict]] = [] # Optional: to keep conversation context

class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = [] # To show which documents were used
    project_context: Optional[str] = None  # Show which project context was used
