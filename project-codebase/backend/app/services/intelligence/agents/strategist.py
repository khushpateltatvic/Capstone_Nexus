from .base import BaseAgent
from app.services.intelligence.prompts import STRATEGIST_TEMPLATE
from typing import Dict, Any

class StrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="strategist")

    async def run(self, document_text: str = "", project_name: str = "Unknown Project") -> Dict[str, Any]:
        inputs = {
            "document_text": document_text,
            "project_name": project_name
        }
        return await self.call_llm(STRATEGIST_TEMPLATE, inputs)
