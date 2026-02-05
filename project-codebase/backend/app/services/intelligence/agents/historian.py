from .base import BaseAgent
from app.services.intelligence.prompts import HISTORIAN_TEMPLATE
from typing import Dict, Any

class HistorianAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="historian")

    async def run(self, document_text: str, rag_context: str = "", project_name: str = "Unknown Project") -> Dict[str, Any]:
        inputs = {
            "document_text": document_text,
            "rag_context": rag_context,
            "project_name": project_name
        }
        return await self.call_llm(HISTORIAN_TEMPLATE, inputs)
