from .base import BaseAgent
from app.services.intelligence.prompts import AUDITOR_TEMPLATE
from typing import Dict, Any

class AuditorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="auditor")

    async def run(self, document_text: str = "", project_name: str = "Unknown Project") -> Dict[str, Any]:
        inputs = {
            "document_text": document_text,
            "project_name": project_name
        }
        return await self.call_llm(AUDITOR_TEMPLATE, inputs)
