"""
Commercial Section API

Endpoints for managing commercial section data:
- SOW data, financial overview, invoices, renewals, revenue channels
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.core.database import get_database
from app.api.v1.endpoints.auth import get_current_user
from app.models.domain.user import User
from app.core.rbac import has_project_access

router = APIRouter()
SECTION = "commercial"


# --- Models ---

class SOWData(BaseModel):
    sow_number: Optional[str] = None
    sow_id: Optional[str] = None
    contract_value: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    payment_terms: Optional[str] = None
    status: Optional[str] = "Active"


class Invoice(BaseModel):
    invoice_number: str
    amount: float
    due_date: Optional[str] = None
    status: str = "pending"  # pending, paid, overdue


class Renewal(BaseModel):
    renewal_date: Optional[str] = None
    proposed_value: Optional[str] = None
    status: Optional[str] = None


class RevenueChannel(BaseModel):
    channel: str
    percentage: float
    notes: Optional[str] = None


# --- Helper ---

async def get_project_section(db, client_id: str, project_id: str, user: User):
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    return project.get(SECTION, {})


async def update_field(db, client_id: str, project_id: str, field: str, value: Any, user: User):
    # Check access first
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not has_project_access(user, project):
        raise HTTPException(status_code=403, detail="You don't have access to this project")
    
    result = await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": {f"{SECTION}.{field}": value, "updated_at": datetime.utcnow().isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "updated", "field": field}


# --- Endpoints ---

@router.get("/{client_id}/{project_id}")
async def get_commercial(client_id: str, project_id: str, current_user: User = Depends(get_current_user)) -> Any:
    """Get entire commercial section."""
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    return {"section": SECTION, "data": data}


@router.put("/{client_id}/{project_id}")
async def update_commercial(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Update entire commercial section."""
    db = await get_database()
    project = await db.projects.find_one({"client_id": client_id, "project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$set": {SECTION: payload, "updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "updated", "section": SECTION}


# --- SOW Data ---

def extract_value(data):
    """Extract value from nested structure or return as-is."""
    if isinstance(data, dict) and "value" in data:
        return data
    return {"value": data} if data else {}

@router.get("/{client_id}/{project_id}/sow")
async def get_sow(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    # Check both active_sow (from RAG) and sow_data (legacy) field names
    sow_data = data.get("active_sow") or data.get("sow_data", {})
    return {"field": "sow_data", "data": extract_value(sow_data)}


@router.put("/{client_id}/{project_id}/sow")
async def update_sow(client_id: str, project_id: str, payload: SOWData, current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "sow_data", payload.dict(), current_user)


# --- Financial Overview ---

@router.get("/{client_id}/{project_id}/financial")
async def get_financial(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    financial_data = data.get("financial_overview", {})
    return {"field": "financial_overview", "data": extract_value(financial_data)}


@router.put("/{client_id}/{project_id}/financial")
async def update_financial(client_id: str, project_id: str, payload: Dict[str, Any], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "financial_overview", payload, current_user)


# --- Invoices ---

@router.get("/{client_id}/{project_id}/invoices")
async def get_invoices(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    invoices_data = data.get("invoices", {})
    if isinstance(invoices_data, dict) and "value" in invoices_data:
        return {"field": "invoices", "data": invoices_data}
    return {"field": "invoices", "data": {"value": invoices_data if isinstance(invoices_data, list) else []}}


@router.put("/{client_id}/{project_id}/invoices")
async def update_invoices(client_id: str, project_id: str, payload: List[Invoice], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "invoices", [i.dict() for i in payload], current_user)


@router.post("/{client_id}/{project_id}/invoices")
async def add_invoice(client_id: str, project_id: str, invoice: Invoice, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.invoices.value": invoice.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "invoice": invoice.dict()}


# --- Renewals ---

@router.get("/{client_id}/{project_id}/renewals")
async def get_renewals(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    renewals_data = data.get("upcoming_renewals", {})
    if isinstance(renewals_data, dict) and "value" in renewals_data:
        return {"field": "upcoming_renewals", "data": renewals_data}
    return {"field": "upcoming_renewals", "data": {"value": renewals_data if isinstance(renewals_data, list) else []}}


@router.put("/{client_id}/{project_id}/renewals")
async def update_renewals(client_id: str, project_id: str, payload: List[Renewal], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "upcoming_renewals", [r.dict() for r in payload], current_user)


@router.post("/{client_id}/{project_id}/renewals")
async def add_renewal(client_id: str, project_id: str, renewal: Renewal, current_user: User = Depends(get_current_user)):
    db = await get_database()
    await db.projects.update_one(
        {"client_id": client_id, "project_id": project_id},
        {"$push": {f"{SECTION}.upcoming_renewals.value": renewal.dict()}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
    )
    return {"status": "added", "renewal": renewal.dict()}


# --- Revenue Channels ---

@router.get("/{client_id}/{project_id}/revenue_channels")
async def get_revenue_channels(client_id: str, project_id: str, current_user: User = Depends(get_current_user)):
    db = await get_database()
    data = await get_project_section(db, client_id, project_id, current_user)
    channels_data = data.get("revenue_channels", {})
    if isinstance(channels_data, dict) and "value" in channels_data:
        return {"field": "revenue_channels", "data": channels_data}
    return {"field": "revenue_channels", "data": {"value": channels_data if isinstance(channels_data, list) else []}}


@router.put("/{client_id}/{project_id}/revenue_channels")
async def update_revenue_channels(client_id: str, project_id: str, payload: List[RevenueChannel], current_user: User = Depends(get_current_user)):
    db = await get_database()
    return await update_field(db, client_id, project_id, "revenue_channels", [r.dict() for r in payload], current_user)
