"""
Client API Endpoints

Provides CRUD operations for clients:
- GET /clients - List all clients
- GET /clients/{client_id} - Get client details
- POST /clients - Create new client
- PUT /clients/{client_id} - Update client
- DELETE /clients/{client_id} - Delete client
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access, is_admin_role

router = APIRouter()


# --- Request/Response Models ---

class ClientCreate(BaseModel):
    client_id: str
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    client_id: str
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    project_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --- Endpoints ---

@router.get("", response_model=List[ClientResponse])
async def list_clients(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List all clients that the user has access to.
    Users can only see clients if they have access to at least one of their projects.
    """
    db = await get_database()
    
    # 1. Get all projects and filter by access
    project_counts = {}
    async for doc in db.projects.find():
        if has_project_access(current_user, doc):
            cid = doc.get("client_id")
            project_counts[cid] = project_counts.get(cid, 0) + 1
    
    accessible_client_ids = set(project_counts.keys())
    
    # 2. Get client details only for accessible clients
    clients = []
    if accessible_client_ids:
        async for client in db.clients.find({"client_id": {"$in": list(accessible_client_ids)}}):
            client_id = client.get("client_id")
            clients.append(ClientResponse(
                client_id=client_id,
                name=client.get("name", client_id),
                industry=client.get("industry"),
                website=client.get("website"),
                notes=client.get("notes"),
                project_count=project_counts.get(client_id, 0),
                created_at=client.get("created_at"),
                updated_at=client.get("updated_at")
            ))
            accessible_client_ids.remove(client_id)
    
    # 3. Add clients that exist in projects but not in clients collection
    for client_id in accessible_client_ids:
        clients.append(ClientResponse(
            client_id=client_id,
            name=client_id,
            project_count=project_counts.get(client_id, 0)
        ))
    
    return clients


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific client's details.
    User must have access to at least one project for this client or be an admin.
    """
    db = await get_database()
    
    # 1. Verify access: User must have access to at least one project for this client
    # Or be an admin of the department the client belongs to (though clients don't have depts, projects do)
    # We'll check if any project for this client is accessible.
    has_access = False
    if current_user.is_superuser:
        has_access = True
    else:
        async for doc in db.projects.find({"client_id": client_id}):
            if has_project_access(current_user, doc):
                has_access = True
                break
    
    if not has_access:
        raise HTTPException(
            status_code=403, 
            detail="You don't have access to this client's projects"
        )
    
    # 2. Get client details
    client = await db.clients.find_one({"client_id": client_id})
    project_count = 0
    async for doc in db.projects.find({"client_id": client_id}):
        if has_project_access(current_user, doc):
            project_count += 1
    
    if not client and project_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return ClientResponse(
        client_id=client_id,
        name=client.get("name", client_id) if client else client_id,
        industry=client.get("industry") if client else None,
        website=client.get("website") if client else None,
        notes=client.get("notes") if client else None,
        project_count=project_count,
        created_at=client.get("created_at") if client else None,
        updated_at=client.get("updated_at") if client else None
    )


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    payload: ClientCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new client.
    """
    db = await get_database()
    
    # Check if client already exists
    existing = await db.clients.find_one({"client_id": payload.client_id})
    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")
    
    now = datetime.utcnow().isoformat()
    client_doc = {
        "client_id": payload.client_id,
        "name": payload.name,
        "industry": payload.industry,
        "website": payload.website,
        "notes": payload.notes,
        "created_at": now,
        "updated_at": now
    }
    
    await db.clients.insert_one(client_doc)
    
    return ClientResponse(
        client_id=payload.client_id,
        name=payload.name,
        industry=payload.industry,
        website=payload.website,
        notes=payload.notes,
        project_count=0,
        created_at=now,
        updated_at=now
    )


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a client's details.
    """
    db = await get_database()
    
    # Build update dict (only include fields that were provided)
    update_data = {k: v for k, v in payload.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    # Upsert - create if doesn't exist
    result = await db.clients.update_one(
        {"client_id": client_id},
        {"$set": update_data},
        upsert=True
    )
    
    # Fetch updated doc
    client = await db.clients.find_one({"client_id": client_id})
    project_count = await db.projects.count_documents({"client_id": client_id})
    
    return ClientResponse(
        client_id=client_id,
        name=client.get("name", client_id),
        industry=client.get("industry"),
        website=client.get("website"),
        notes=client.get("notes"),
        project_count=project_count,
        created_at=client.get("created_at"),
        updated_at=client.get("updated_at")
    )


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    delete_projects: bool = False,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Delete a client. Optionally delete all associated projects.
    """
    db = await get_database()
    
    # Check if client has projects
    project_count = await db.projects.count_documents({"client_id": client_id})
    
    if project_count > 0 and not delete_projects:
        raise HTTPException(
            status_code=400, 
            detail=f"Client has {project_count} projects. Set delete_projects=true to delete them."
        )
    
    # Delete projects if requested
    if delete_projects:
        await db.projects.delete_many({"client_id": client_id})
    
    # Delete client
    result = await db.clients.delete_one({"client_id": client_id})
    
    return {
        "status": "deleted",
        "client_id": client_id,
        "projects_deleted": project_count if delete_projects else 0
    }
