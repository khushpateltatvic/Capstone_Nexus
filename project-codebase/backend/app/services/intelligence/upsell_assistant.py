import json
from datetime import datetime
from typing import Dict, List, Any
from app.core.database import get_database
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logging_config import logger

UPSELL_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """You are a Senior Account Strategist for Tatvic Analytics.
    
    YOUR GOAL: Identify strategic upsell opportunities for the client based on our specific service offerings.
    
    --- APPROVED SERVICE CATALOG (Only suggest these) ---
    - Agentic AI & GenAI Solutions
    - Data Marketing & Activation
    - Data Migration to GCP
    - Data Analytics & Engineering
    - Google Analytics 4 (GA4) Implementation & Audit
    - Cloud Infrastructure (GCP)
    - Conversion Rate Optimization (CRO)
    - Media Activations
    - DV360 Managed Services
    - DV360 Self Serve Support
    - Advanced Funnel Optimization
    - Google Tag Manager 360 (GTM 360)
    - Looker BI & Visualization
    - Google Cloud Platform (GCP) Managed Services
    - Consent Management Platform (CMP) Implementation
    -----------------------------------------------------

    INPUTS:
    1. CURRENT SERVICES (What we strictly do now).
    2. NEWS/EVENTS (External context).
    3. STRATEGY (Client goals).
    
    OUTPUT FORMAT:
    Generate 3 specific "Strategic Hooks" or "Proposals".
    
    CRITICAL RULE:
    Each proposal MUST map to one of the services in the Approved Service Catalog above.
    
    RETURN STRICT JSON:
    [
      {{
        "service_category": "One of the catalog items above",
        "title": "Short Hook Title",
        "description": "Why this opportunity exists...",
        "pitch": "How to pitch it to the client...",
        "potential_value": "High/Medium/Low",
        "rationale": "Connection between News X and Service Y"
      }}
    ]
    """),
    ("user", """Client: {client_name}
    Project: {project_name}
    
    --- CURRENT COMMERCIALS (Services we ALREADY provide) ---
    {commercial_data}
    
    --- RECENT NEWS (External Context) ---
    {news_data}
    
    --- STRATEGY (Client Goals) ---
    {strategy_data}
    """)
])

async def generate_upsell_opportunities(project_id: str) -> List[Dict[str, Any]]:
    """
    Analyzes project data to generate upsell opportunities.
    """
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise ValueError("Project not found")
        
    client = await db.clients.find_one({"client_id": project.get("client_id")})
    client_name = client.get("name") if client else "Unknown Client"
    
    # Prepare Data
    commercial = project.get("commercial", {})
    news = project.get("news", [])[:5] # Last 5 news items
    strategy = project.get("strategy", {})
    
    # Format inputs
    commercial_str = json.dumps(commercial, default=str)
    news_str = "\n".join([f"- {n.get('title')} ({n.get('date')})" for n in news]) if news else "No recent news found."
    strategy_str = json.dumps(strategy, default=str)
    
    try:
        llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.5
        )
        
        chain = UPSELL_TEMPLATE | llm
        
        response = await chain.ainvoke({
            "client_name": client_name,
            "project_name": project.get("name", "Unknown"),
            "commercial_data": commercial_str,
            "news_data": news_str,
            "strategy_data": strategy_str
        })
        
        # Parse output
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        opportunities = json.loads(content)
        
        # Save to Project
        await db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "intelligence.upsell_opportunities": list(opportunities),
                    "intelligence.upsell_updated_at": datetime.utcnow()
                }
            }
        )
        
        return opportunities

    except Exception as e:
        logger.error(f"Error generating upsell opportunities: {e}")
        return []
