from .base import BaseAgent
from app.services.intelligence.prompts import ROUTER_TEMPLATE
from typing import Dict, Any

class RouterAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="router")

    async def analyze_document(self, text: str, metadata: dict) -> Dict[str, Any]:
        first_1000 = text[:1000]
        inputs = {
            "first_1000_chars": first_1000,
            "metadata": str(metadata)
        }
        return await self.call_llm(ROUTER_TEMPLATE, inputs)
