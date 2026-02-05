import json
from datetime import datetime
from app.core.database import get_database
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.core.logging_config import logger

# New Research-Focused Prompt
MARKETING_RESEARCH_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """You are an expert Marketing Strategist & Researcher.
    
    YOUR GOAL: Generate a comprehensive marketing profile for the Project "{project_name}" (Client: "{client_name}").
    
    SOURCES OF TRUTH (in order of priority):
    1. The provided Project Context text (most important).
    2. YOUR INTERNAL KNOWLEDGE & TRAINING DATA (Web Knowledge).
       - Use this to fill in gaps (like Brand Colors or Public References) if they are missing from the text.
    
    EXTRACT & ANALYZE THESE FIELDS:
    
    1. Brand Guidelines:
       - Primary and Secondary Core Hex Codes.
       - Typography/Fonts used.
       - Brand Voice/Tone.
       - If not in context, infer from your knowledge of the "{client_name}" brand.
       
    2. Success Stories / Case Studies:
       - Focus on stories related to "{project_name}" if available.
       - Otherwise, include general success stories for "{client_name}".
       - Format: Title + Brief Description.
       
    3. Testimonials:
       - Quotes relevant to this project or client.
       - Format: Name + Quote.
       
    4. Public References:
       - Links to blogs, news articles, or webinars involving "{client_name}" or "{project_name}".
       
    RETURN STRICT JSON:
    {{
      "brand_guidelines": {{
         "primary_color": "#HEX",
         "secondary_color": "#HEX",
         "typography": "Font Name",
         "tone": "Professional/Playful/etc"
      }},
      "success_stories": [
         {{"title": "Story Title", "description": "What they achieved..."}}
      ],
      "testimonials": [
         {{"from": "Person Name", "quote": "Quote..."}}
      ],
      "public_references": [
         {{"type": "Article", "title": "Title", "url": "URL"}}
      ]
    }}
    
    If you absolutely cannot find or infer data for a field, return an empty list/object for it.
    """),
    ("user", """Project: {project_name}
    Client: {client_name}
    Context:
    {document_text}""")
])

async def generate_marketing_intelligence(project_id: str, client_id: str, client_name: str):
    """
    Generates marketing intelligence using both Project Context and LLM's Internal Knowledge.
    """
    
    # 1. Fetch Project for Context
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise ValueError("Project not found")
        
    # 2. Construct Context
    context_parts = []
    
    # Universal Context
    univ = project.get("universal_context", {})
    if univ:
        context_parts.append(f"--- UNIVERSAL CONTEXT ---\n{json.dumps(univ, default=str)}")
        
    # Strategy
    strat = project.get("strategy", {})
    if strat:
        context_parts.append(f"--- STRATEGY ---\n{json.dumps(strat, default=str)}")

    document_text = "\n\n".join(context_parts)
    if not document_text:
        document_text = "No specific project document provided. Relies on internal knowledge."

    # 3. Call Gemini
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.4, # Slightly higher temp for "creative" retrieval/inference
            convert_system_message_to_human=True
        )
        
        chain = MARKETING_RESEARCH_TEMPLATE | llm
        
        # Invoke
        response = await chain.ainvoke({
            "project_name": project.get("name"),
            "client_name": client_name,
            "document_text": document_text
        })
        
        # Parse JSON
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        
        # 4. Update Project Marketing Section
        marketing_update = {}
        
        if "brand_guidelines" in data and data["brand_guidelines"]:
            marketing_update["marketing.brand_guidelines"] = {"value": data["brand_guidelines"]}
            
        if "success_stories" in data and data["success_stories"]:
            marketing_update["marketing.success_stories"] = {"value": data["success_stories"]}
            
        if "testimonials" in data and data["testimonials"]:
            marketing_update["marketing.testimonials"] = {"value": data["testimonials"]}
            
        if "public_references" in data and data["public_references"]:
            marketing_update["marketing.public_references"] = {"value": data["public_references"]}
            
        if marketing_update:
            marketing_update["updated_at"] = datetime.utcnow()
            await db.projects.update_one({"project_id": project_id}, {"$set": marketing_update})
            logger.info(f"Generated [Marketing] for Client: {client_name} ({client_id}) | Project: {project.get('name')}")
            
        return data

    except Exception as e:
        logger.error(f"Error generating marketing intelligence: {e}")
        raise e
