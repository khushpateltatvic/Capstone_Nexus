import httpx
from datetime import datetime
from typing import List, Dict, Optional
from app.core.config import settings
from app.core.logging_config import logger
from app.core.database import get_database

async def fetch_project_news(project_id: str) -> List[Dict]:
    """
    Fetches news specific to the project's client and domain (competitors/keywords).
    Stores results in the Project document.
    """
    if not settings.GNEWS_API_KEY:
        logger.warning("GNEWS_API_KEY not set. Skipping news fetch.")
        return []

    # 1. Fetch Project & Client
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise ValueError("Project not found")
        
    client = await db.clients.find_one({"client_id": project.get("client_id")})
    client_name = client.get("name") if client else project.get("client_id")
    
    # 2. Extract Context for Search
    competitors = []
    keywords = []
    
    # Strategy -> Competitors
    strat = project.get("strategy", {})
    if strat and "competitors" in strat:
        comps = strat["competitors"]
        if isinstance(comps, list):
            competitors = [c.get("name") for c in comps if isinstance(c, dict) and "name" in c]
            
    # Universal Context -> Keywords (Simple heuristic: Project Name parts?)
    # For now, let's stick to Client Name + Project Name (if meaningful)
    # Cleaning project name: "Tatvic - Project Nexus" -> "Nexus" might be too generic.
    # Safe bet: Client Name is the primary anchor.
    
    # 3. Construct Queries
    # We want news about the Client AND (Project Domain OR Competitors)
    # GNews "q" parameter supports AND/OR/NOT
    # Query 1: Client Specific
    q_client = f'"{client_name}"'
    
    # Query 2: Client vs Competitors (if any)
    # q_competitors = f'"{client_name}" AND ("{comp1}" OR "{comp2}")'
    
    queries = [q_client]
    if competitors:
        comp_str = " OR ".join([f'"{c}"' for c in competitors[:3]]) # Limit to 3
        queries.append(f'"{client_name}" AND ({comp_str})')

    all_articles = []
    seen_urls = set()
    
    async with httpx.AsyncClient() as client:
        for query in queries:
            try:
                # GNews Free Tier: 10 requests/day? No, usually 100/day.
                # max 10 results.
                url = "https://gnews.io/api/v4/search"
                params = {
                    "q": query,
                    "lang": "en",
                    "max": 5,
                    "apikey": settings.GNEWS_API_KEY,
                    "sortby": "publishedAt"
                }
                
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    articles = data.get("articles", [])
                    for art in articles:
                        if art["url"] not in seen_urls:
                            all_articles.append({
                                "title": art["title"],
                                "description": art["description"],
                                "url": art["url"],
                                "source": art["source"]["name"],
                                "published_at": art["publishedAt"],
                                "search_query": query
                            })
                            seen_urls.add(art["url"])
                else:
                    logger.error(f"GNews API Error: {resp.status_code} - {resp.text}")
                    
            except Exception as e:
                logger.error(f"News fetch failed for query '{query}': {e}")

    # 4. Filter & Sort
    # Sort by date (newest first)
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    top_articles = all_articles[:10] # Keep top 10 unique
    
    # 5. Update Project
    if top_articles:
        await db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "news": top_articles,
                    "news_last_updated": datetime.utcnow()
                }
            }
        )
        logger.info(f"Updated news for project {project_id} ({len(top_articles)} articles)")
        
    return top_articles
