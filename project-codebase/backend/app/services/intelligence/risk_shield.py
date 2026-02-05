from typing import Dict, List, Any
import json
from datetime import datetime
from app.core.database import get_database
from app.services.ingestion.basecamp import basecamp_service
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logging_config import logger

RISK_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """You are a Client Health Analyst.
    Analyze the sentiment of the following recent communications.
    
    INPUT: A list of recent messages/comments.
    
    TASK:
    1. Detect ANY signs of friction, delay, frustration, or confusion.
    2. Assign a specific "Risk Score" (0-100, where 100 is high risk).
    3. Summarize the specific concerns.
    
    RETURN STRICT JSON:
    {{
      "risk_score": 15,
      "risk_level": "Low/Medium/High",
      "sentiment": "Positive/Neutral/Negative",
      "flags": ["Mentioned delay", "Confused about pricing"],
      "summary": "Client is happy but asked about timeline."
    }}
    """),
    ("user", """Recent Activity:
    {activity_text}
    """)
])

async def analyze_project_risk(project_id: str) -> Dict[str, Any]:
    """
    Analyzes project risk based on Basecamp activity.
    """
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise ValueError("Project not found")
        
    # Fetch Basecamp Activity
    # Assuming project_id in DB matches Basecamp ID, or we store basecamp_id in project
    # Project model structure check? 
    # Usually we rely on startup automation mapping. 
    # Let's assume project_id IS the basecamp ID for now, or use mapped field.
    # In `basecamp.py`, we use the ID from settings list. 
    # For now, pass project_id.
    
    activity = []
    try:
        activity = await basecamp_service.get_recent_activity(project_id, limit=15)
    except Exception as e:
        logger.warning(f"Failed to fetch Basecamp activity for {project_id}: {e}")
        
    if not activity:
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "sentiment": "No Data",
            "flags": [],
            "summary": "No recent activity found to analyze."
        }
        
    activity_text = "\n---\n".join(activity)
    
    try:
        llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.0
        )
        
        chain = RISK_TEMPLATE | llm
        
        response = await chain.ainvoke({
            "activity_text": activity_text
        })
        
        # Parse output
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        risk_data = json.loads(content)
        
        # Save to Project
        await db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "intelligence.risk_analysis": risk_data,
                    "intelligence.risk_updated_at": datetime.utcnow()
                }
            }
        )
        
        return risk_data

    except Exception as e:
        logger.error(f"Error generating risk analysis: {e}")
        return {"error": str(e)}
