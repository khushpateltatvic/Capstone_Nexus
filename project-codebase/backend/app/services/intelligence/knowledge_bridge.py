from typing import Dict, List, Any
from app.models.domain.core_entities import Project
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from app.core.config import settings
from app.core.logging_config import logger
from app.core.database import get_database
import json

MATCH_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """You are a Knowledge Management Specialist.
    
    YOUR GOAL: Connect "Client Goals" from the Target Project to "Success Stories" from other projects.
    
    INPUT:
    1. Target Project: {target_name}
    2. Target Goals: {target_goals}
    3. Available Success Stories (from other teams):
       {stories_list}
       
    TASK:
    Identify matches where a Success Story proves we can achieve a Target Goal.
    
    RETURN STRICT JSON:
    [
      {{
        "target_goal": "Optimize cloud costs",
        "matched_story": "Project Alpha: Reduced AWS spend by 30%",
        "reason": "Both involve cloud cost optimization...",
        "source_project": "Project Alpha",
        "confidence": "High"
      }}
    ]
    
    Return [] if no good matches found.
    """),
    ("user", """Target: {target_name}
    Goals: {target_goals}
    Stories:
    {stories_list}""")
])

async def find_knowledge_proposals(project_id: str) -> List[Dict[str, Any]]:
    """
    Finds matches between this project's goals and other projects' success stories.
    """
    db = await get_database()
    
    # 1. Get Target Project (Raw dict to access unmodeled sections)
    target = await db.projects.find_one({"project_id": project_id})
    if not target:
        logger.error(f"Knowledge Bridge: Project {project_id} not found")
        raise ValueError("Project not found")
        
    strategy = target.get("strategy") or {}
    # Broaden goal search: check roadmap, goals_roadmap, and also keys in the strategy dict itself
    goals = strategy.get("goals_roadmap") or strategy.get("roadmap") or []
    
    # If it's a dict (Datapoint wrapper), extract value
    if isinstance(goals, dict):
        goals = goals.get("value", [])
        
    if not goals:
        # Fallback: look for other potential goal fields
        goals = strategy.get("objectives", []) or strategy.get("client_goals", [])
        if isinstance(goals, dict): goals = goals.get("value", [])

    logger.info(f"Knowledge Bridge: Found {len(goals)} goals for project {project_id}")
    
    if not goals:
        return []
        
    # 2. Get All Other Projects with Success Stories
    # Loosen filter: check for exists, not just size
    cursor = db.projects.find({
        "project_id": {"$ne": project_id},
        "marketing.success_stories": {"$exists": True}
    })
    
    stories_inventory = []
    async for p in cursor:
        if not p:
            continue
        p_name = p.get("name", "Unknown Project")
        marketing = p.get("marketing") or {}
        
        # Handle both raw list and Datapoint wrapper
        raw_stories = marketing.get("success_stories") or {}
        if isinstance(raw_stories, dict):
            stories = raw_stories.get("value", [])
        else:
            stories = raw_stories if isinstance(raw_stories, list) else []
        
        if stories:
            for s in stories:
                if isinstance(s, dict):
                    stories_inventory.append(f"Project: {p_name} | Story: {s.get('title', 'N/A')} - {s.get('description', 'N/A')}")
                
    if not stories_inventory:
        return []
        
    # Limit context size (take top 20 stories for now)
    stories_text = "\n".join(stories_inventory[:20])
    
    formatted_goals = []
    for g in goals:
        if isinstance(g, dict):
            formatted_goals.append(g.get("goal") or g.get("title", ""))
        elif isinstance(g, str):
            formatted_goals.append(g)
            
    goals_text = "\n".join([f"- {gt}" for gt in formatted_goals if gt])
    
    logger.info(f"Knowledge Bridge: Matching project {target.get('name')} with {len(stories_inventory)} available stories")
    
    try:
        llm = ChatGroq(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.0
        )
        
        chain = MATCH_TEMPLATE | llm
        
        response = await chain.ainvoke({
            "target_name": target.get("name", "Unknown"),
            "target_goals": goals_text,
            "stories_list": stories_text
        })
        
        # Parse output
        content = response.content
        logger.debug(f"Knowledge Bridge: Raw LLM Output: {content}")
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        matches = json.loads(content)
        
        # Save? Maybe not needed to persist, calculated on demand.
        # But let's cache it.
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"intelligence.knowledge_matches": matches}}
        )
        
        return matches

    except Exception as e:
        logger.error(f"Error finding knowledge matches: {e}")
        return []
