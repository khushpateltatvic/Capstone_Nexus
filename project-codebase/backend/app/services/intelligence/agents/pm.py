from .base import BaseAgent
from app.services.intelligence.prompts import PM_TEMPLATE
from typing import Dict, Any

class PMAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="pm")

    async def run(self, document_text: str = "", existing_tasks: str = "[]", project_name: str = "Unknown Project") -> Dict[str, Any]:
        inputs = {
            "document_text": document_text,
            "existing_tasks": existing_tasks,
            "project_name": project_name
        }
        return await self.call_llm(PM_TEMPLATE, inputs)
