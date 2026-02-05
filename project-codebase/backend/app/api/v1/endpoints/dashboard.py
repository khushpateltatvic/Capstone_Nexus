from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Dict
from app.core.database import get_database
from app.models.domain.project import Client, Project
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access

router = APIRouter()

@router.get("/{client_id}/dashboard")
async def get_client_dashboard(
    client_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get full dashboard for a client from MongoDB.
    Protected by JWT.
    """
    database = await get_database()
    
    # 1. Fetch Projects (Primary Discovery)
    projects_cursor = database.projects.find({"client_id": client_id})
    projects = []
    async for doc in projects_cursor:
        if has_project_access(current_user, doc):
            # Convert ObjectId to string for Pydantic/JSON serialization
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            projects.append(doc)
    
    if not projects and not current_user.is_superuser:
        # If no projects are accessible for this client, verify if client exists
        # but don't leak its existence if user has zero access to it.
        # Check if the user has access to *any* project for this client.
        has_any_access = False
        async for doc in database.projects.find({"client_id": client_id}):
             if has_project_access(current_user, doc):
                 has_any_access = True
                 break
        if not has_any_access:
            raise HTTPException(status_code=403, detail="You don't have access to this client")
    
    # 2. Fetch Client Metadata (Optional/Rollup)
    client_doc = await database.clients.find_one({"client_id": client_id})
    
    return {
        "client_id": client_id,
        "name": client_doc.get("name", "New Client") if client_doc else "New Client",
        "projects": projects,
        "status": "Active" if projects else "Initialized"
    }

@router.get("/{client_id}/operations")
async def get_client_operations(
    client_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get aggregated operations view.
    """
    database = await get_database()
    projects = []
    async for doc in database.projects.find({"client_id": client_id}):
        if has_project_access(current_user, doc):
            projects.append(doc)
    
    if not projects and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="You don't have access to this client")
    
    ops_view = []
    for p in projects:
        ops = p.get("operations", {})
        
        # Handle cases where operations might be None or partial
        traffic_val = "Unknown"
        traffic_data = ops.get("traffic_light")
        if isinstance(traffic_data, dict):
            traffic_val = traffic_data.get("value", "Unknown")
            
        ops_view.append({
            "project_name": p.get("name"),
            "traffic_light": traffic_val,
            "blockers_count": len(ops.get("blockers", []))
        })
        
    return {"client_id": client_id, "operations_summary": ops_view}
