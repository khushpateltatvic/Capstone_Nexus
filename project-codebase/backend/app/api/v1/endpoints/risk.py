from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.services.intelligence.risk_shield import analyze_project_risk
from app.models.domain.core_entities import Project
from app.core.database import get_database

router = APIRouter()

@router.post("/{project_id}/analyze")
async def analyze_risk(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Triggers AI to analyze project risk/sentiment from Basecamp activity.
    """
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Access check...
    
    result = await analyze_project_risk(project_id)
    
    return {
        "status": "success",
        "project_id": project_id,
        "data": result
    }

@router.get("/{project_id}")
async def get_project_risk(
    project_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get stored risk analysis."""
    db = await get_database()
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    intelligence = project.get("intelligence", {})
    risk_analysis = intelligence.get("risk_analysis", {})
    
    # Bridge: Fallback to basic extraction from Ops/Universal context
    if not risk_analysis:
        ops = project.get("operations", {})
        # Extract traffic light value (strip Datapoint wrapper if exists)
        tl_data = ops.get("traffic_light")
        traffic_light = tl_data.get("value") if isinstance(tl_data, dict) else (tl_data or "Green")
        
        # Extract health score from client profile
        uc = project.get("universal_context", {})
        cp_data = uc.get("client_profile")
        client_profile = cp_data.get("value") if isinstance(cp_data, dict) else (cp_data or {})
        health_score = client_profile.get("health_score", "Good")
        
        # Extract indicators/flags from blockers
        blockers_data = ops.get("blockers")
        blockers = blockers_data.get("value") if isinstance(blockers_data, dict) else (blockers_data or [])
        flags = [b.get("issue") for b in blockers if isinstance(b, dict) and b.get("issue")]
        
        risk_analysis = {
            "risk_level": "Critical" if traffic_light == "Red" else "Medium" if traffic_light == "Yellow" else "Low",
            "sentiment": "Neutral",
            "summary": f"Initial assessment based on project health ({health_score}) and status ({traffic_light}). Click 'Generate Analysis' for deep insight.",
            "indicators": flags or ["No critical technical blockers detected."],
            "recommendations": ["Trigger deep sentiment analysis for specific mitigation strategies."]
        }

    return {
        "project_id": project_id,
        "last_updated": intelligence.get("risk_updated_at"),
        "data": risk_analysis
    }
