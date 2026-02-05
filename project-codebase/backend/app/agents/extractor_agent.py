import json
from typing import Optional, Dict, List, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from app.core.config import settings
from app.core.logging_config import logger

def get_extractor_chain(schema_desc: str):
    llm = ChatGroq(temperature=0, model_name=settings.GROQ_MODEL_NAME, api_key=settings.GROQ_API_KEY)
    
    # Optimized State-Manager Prompt
    system_prompt = """You are a precise data state manager with strict email validation rules.
    You will receive the CURRENT_STATE (JSON) of a project section and NEW_INPUT (Text).
    
    ### CRITICAL EMAIL RULES:
    - Internal team members: MUST have @tatvic.com email addresses ONLY
    - External stakeholders/POCs: MUST NOT have @tatvic.com email addresses
    - All stakeholder and POC entries MUST include email addresses
    - If email is not provided in text, mark as null as placeholder
    
    ### PROJECT HEALTH STATUS RULES:
    - Be realistic in health assessments based on actual project indicators
    - "Excellent": Active communication, on-time deliveries, positive feedback, no blockers
    - "Good": Regular communication, mostly on track, minor issues resolved quickly  
    - "At Risk": Communication gaps, delayed deliveries, unresolved blockers, client concerns
    - "Poor": Minimal communication, major delays, critical blockers, client dissatisfaction
    
    ### TASK:
    Merge the NEW_INPUT into the CURRENT_STATE to produce an UPDATED_STATE.
    1. If CURRENT_STATE is null/empty, extract data from NEW_INPUT as the initial state.
    2. If CURRENT_STATE exists, UPDATE or APPEND new information from NEW_INPUT.
    3. Maintain existing history (e.g. don't delete old tasks/goals unless the text says they are replaced).
    4. Normalize names and ensure the output is VALID JSON matching the SCHEMA.
    5. Validate all email addresses according to the rules above.
    6. Return ONLY the UPDATED_STATE JSON. No conversational text.
    
    ### TARGET SCHEMA:
    {schema}
    
    ### CURRENT_STATE:
    {current_state}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "NEW_INPUT:\n{text}")
    ])
    
    def strip_markdown(text):
        if hasattr(text, "content"): text = text.content
        text = text.strip()
        # Find JSON start and end
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        
        # Remove inline comments (// ...) which are invalid JSON but common in LLM output
        import re
        text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)
        
        # specific fix for LLM using NULL instead of null
        text = text.replace("NULL", "null")
        return text

    chain = prompt | llm | strip_markdown | JsonOutputParser()
    return chain

async def extract_data(text: str, section_id: int, existing_context: Optional[dict] = None):
    # Comprehensive Schemas based on User Request
    schema_map = {
        1: """
        {
            "summary": "1.1 Summary/Background of Account",
            "timeline": [{"date": "ISO", "event": "Milestone", "significance": "High/Medium/Low"}], // 1.2 Timeline
            "engagement_type": "FTE/Concierge/Retainer/Project-based/Other", // 1.3
            "client_profile": { 
                "name": "Client Company Name", 
                "industry": "Industry", 
                "start_date": "ISO", 
                "health_score": "Excellent/Good/At Risk/Poor", // Realistic assessment
                "company_size": "Enterprise/Mid-Market/SMB",
                "headquarters": "Location",
                "website": "URL"
            }, // 1.4
            "internal_squad": [{"name": "Name", "role": "Role", "email": "name@tatvic.com"}], // 1.5 - Only @tatvic.com emails
            "poc_map": [{"name": "Full Name", "role": "Role Title", "email": "email@clientdomain.com", "phone": "Phone", "department": "Department"}], // 1.6 - External POCs only with full contact info
            "pocs": [{"name": "Full Name", "role": "Specific Role Title", "email": "email@clientdomain.com", "phone": "Phone number", "company": "Client Company", "department": "Department/Division"}], // Enhanced POC mapping with complete contact details
            "communication_hygiene": { 
                "last_email": "ISO", 
                "last_meeting": "ISO", 
                "response_time_avg": "X hours/days", 
                "meeting_frequency": "Daily/Weekly/Bi-weekly/Monthly",
                "preferred_communication": "Email/Slack/Teams/Phone",
                "escalation_path": "Who to contact for urgent issues"
            }, // 1.7 - Enhanced communication tracking
            "important_notes": "1.8 Critical information about client relationship, preferences, history",
            "google_workspace_team": "1.9 Google Team Members and shared resources",
            "account_id": "External ID if present",
            "contract_details": {
                "type": "MSA/SOW/Retainer",
                "value": "Contract value if known",
                "duration": "Contract duration",
                "renewal_date": "Next renewal date"
            }
        }
        """,
        2: """
        {
            "status": "Green/Amber/Red", // 2.1 Project Health Status - Be realistic based on actual project conditions
            "reason": "Specific reason for current health status based on real indicators",
            "health_indicators": {
                "communication_frequency": "Daily/Weekly/Monthly/Poor",
                "deliverable_timeline": "On Track/Delayed/At Risk",
                "client_satisfaction": "High/Medium/Low/Unknown",
                "technical_progress": "Smooth/Some Issues/Major Blockers",
                "budget_status": "Under Budget/On Budget/Over Budget/Unknown"
            },
            "tasks": [{"title": "Task", "status": "Upcoming/Ongoing/Completed/Blocked", "due": "ISO", "owner": "Name", "priority": "High/Medium/Low"}], // 2.2 Task Board
            "blockers": [{"description": "Blocker description", "severity": "Critical/High/Medium/Low", "impact": "Impact on project", "owner": "Responsible person"}], // 2.3 - Detailed blocker objects
            "recent_interactions": [{"title": "Meeting Title", "date": "ISO", "notes": "Summary", "attendees": ["Name1", "Name2"], "action_items": ["Action item"]}], // 2.4 - Enhanced interactions
            "interactions": [{"title": "Meeting Title", "date": "ISO", "notes": "Summary", "attendees": ["Name1", "Name2"]}], 
            "engagement_status": "Discovery/Active_Delivery/Maintenance/At_Risk/Churned/Paused", // 2.5 - More specific statuses
            "stakeholder_name": "Reporter Name",
            "stakeholder_role": "Reporter Role", 
            "stakeholder_email": "Reporter Email"
        }
        """,
        3: """
        {
            "tech_stack": [{"name": "Tech", "status": "Active/Planned/Deprecated"}], // 3.1 Matrix
            "credentials": [{"system": "System Name", "access": "Read/Write/Admin"}], // 3.2 Access
            "implementation_log": ["Task Completed"], // 3.3
            "experiments": [{"name": "Experiment Name", "result": "Result"}], // 3.4 Results
            "technology": "Main tech (legacy compat)",
            "category": "Frontend/Backend/etc"
        }
        """,
        4: """
        {
            "active_sow": { "scope": "Summary", "value": 0.0, "start": "ISO", "end": "ISO" }, // 4.1
            "financials": { "revenue": 0.0, "currency": "USD" }, // 4.2
            "invoicing": { "status": "Paid/Pending/Overdue", "next_date": "ISO" }, // 4.3
            "renewals": [{"service": "Service Name", "date": "ISO"}], // 4.4
            "revenue_channels": ["Channel Name"], // 4.5
            "value": 0.0, "scope_summary": "Legacy compat"
        }
        """,
        5: """
        {
            "stakeholders": [{ 
                "name": "Full Name", 
                "role": "DecisionMaker/Influencer/Supporter/Controller/Technical Lead/Business Owner", // 5.1
                "sentiment": "Champion/Supporter/Neutral/Skeptic/Blocker", // 5.1
                "influence": "High/Medium/Low",
                "email": "email@clientdomain.com", // REQUIRED - Must be external non-Tatvic email
                "phone": "Phone number if available",
                "company": "Client company name",
                "department": "Department/Division",
                "reports_to": "Manager Name", // 5.2 Hierarchy
                "last_interaction": "ISO date of last contact",
                "notes": "Important notes about this stakeholder"
            }],
            "stakeholder_map": [{ 
                "name": "Full Name", 
                "role": "Specific Role Title", 
                "email": "email@clientdomain.com", // MUST be external email only - NO @tatvic.com
                "phone": "Phone number", 
                "sentiment": "Champion/Supporter/Neutral/Skeptic/Blocker", 
                "influence": "High/Medium/Low",
                "company": "Client company name"
            }], // CRITICAL: Only external stakeholders, no internal @tatvic.com emails
            "client_goals": [{"goal": "Specific Goal Description", "timeline": "Timeline with dates", "priority": "High/Medium/Low", "owner": "Stakeholder responsible"}], // 5.3
            "goals": [{"goal": "Goal", "timeline": "Timeline", "priority": "High/Medium/Low"}], // match model attribute
            "upsell_opportunities": [{"opportunity": "Detailed Description", "value": 0.0, "timeline": "When this could happen", "likelihood": "High/Medium/Low", "champion": "Who supports this"}], // 5.4 - Enhanced upsell tracking
            "competitors": [{"name": "Competitor Name", "threat": "High/Medium/Low", "strengths": "What they do well", "weaknesses": "Where we can win"}], // 5.5 - Enhanced competitor analysis
            "platform_ecosystem": [{"platform": "Platform Name", "usage": "How they use it", "integration_level": "Deep/Surface/Planned"}], // 5.6 - Enhanced ecosystem mapping
            "goal": "Legacy goal extract",
            "priority": "High/Medium/Low"
        }
        """,
        6: """
        {
            "brand_guidelines": { "link": "URL", "colors": ["Hex"] }, // 6.1
            "success_stories": [{"title": "Story Title", "details": "Details"}], // 6.2
            "testimonials": [{"quote": "Quote", "author": "Name"}], // 6.3
            "public_references": [{"link": "URL", "type": "Press/Article"}], // 6.4
            "story": "Legacy"
        }
        """,
        7: """
        {
            "feedback": { "raw": "Text", "rephrased": "Polite version", "sentiment": "Pos/Neg" }, // 7.1
            "subscriptions": [{"goal": "Key Goal", "status": "Active"}], // 7.2
            "documents": [{"title": "Doc Name", "link": "URL"}], // 7.3
            "additional_emails": ["email@example.com"], // 7.4
            "note": "Legacy note"
        }
        """
    }
    
    schema_desc = schema_map.get(section_id, "{}")
    
    try:
        chain = get_extractor_chain(schema_desc)
        # Pass existing context to LLM
        ctx_str = json.dumps(existing_context, indent=2) if existing_context else "null (Initial Extraction)"
        
        result = await chain.ainvoke({
            "schema": schema_desc, 
            "text": text,
            "current_state": ctx_str
        })
        logger.debug(f"Extractor LLM updated state for Section {section_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"State Update Error for Section {section_id}: {e}")
        return {"error": "Failed to update state", "raw_text": text}
