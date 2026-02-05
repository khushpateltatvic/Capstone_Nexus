from .base import BaseAgent
from app.services.intelligence.prompts import TECH_LEAD_TEMPLATE
from typing import Dict, Any

class TechLeadAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="tech_lead")

    async def run(self, document_text: str = "", project_name: str = "Unknown Project") -> Dict[str, Any]:
        inputs = {
            "document_text": document_text,
            "project_name": project_name
        }
        return await self.call_llm(TECH_LEAD_TEMPLATE, inputs)
