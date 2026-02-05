from typing import Optional, List, Any, Union
from beanie import PydanticObjectId
from datetime import date
from pydantic import BaseModel, Field, model_validator, ConfigDict

# SOW Schemas
class ActiveSOWBase(BaseModel):
    scope_summary: str
    start_date: date
    end_date: date
    value: Optional[float] = None
    billing_model: Optional[str] = "Fixed"

class ActiveSOWCreate(ActiveSOWBase):
    client_id: str
    client_contact_email: Optional[str] = None
    account_manager_email: Optional[str] = None

class ActiveSOWRead(ActiveSOWBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    client_contact_id: Optional[Union[PydanticObjectId, str]] = None
    account_manager_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "client_contact") and data.client_contact:
            result["client_contact_id"] = str(data.client_contact.id) if hasattr(data.client_contact, "id") else str(data.client_contact)
        if hasattr(data, "account_manager") and data.account_manager:
            result["account_manager_id"] = str(data.account_manager.id) if hasattr(data.account_manager, "id") else data.account_manager
        return result

# Renewal Schemas
class RenewalBase(BaseModel):
    renewal_date: date
    renewal_risk: str # Low | Medium | High

class RenewalCreate(RenewalBase):
    client_id: str
    renewal_contact_email: Optional[str] = None
    account_manager_email: Optional[str] = None

class RenewalRead(RenewalBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    renewal_contact_id: Optional[Union[PydanticObjectId, str]] = None
    account_manager_id: Optional[Union[PydanticObjectId, str]] = None

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        if hasattr(data, "renewal_contact") and data.renewal_contact:
            result["renewal_contact_id"] = str(data.renewal_contact.id) if hasattr(data.renewal_contact, "id") else data.renewal_contact
        if hasattr(data, "account_manager") and data.account_manager:
            result["account_manager_id"] = str(data.account_manager.id) if hasattr(data.account_manager, "id") else data.account_manager
        return result

# Financial Overview
class FinancialBase(BaseModel):
    total_contract_value: float
    monthly_recurring_revenue: float
    revenue_channels: List[str] = []
    currency: str = "USD"

class FinancialCreate(FinancialBase):
    client_id: str

class FinancialRead(FinancialBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]
    last_updated: date

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result

# Invoicing Status
class InvoicingBase(BaseModel):
    pending_amount: float
    overdue_amount: float
    status: str # UpToDate | Behind | Disputed
    last_invoice_date: Optional[date] = None
    next_invoice_date: Optional[date] = None

class InvoicingCreate(InvoicingBase):
    client_id: str

class InvoicingRead(InvoicingBase):
    model_config = ConfigDict(from_attributes=True)
    id: Union[PydanticObjectId, str]
    client_id: Union[PydanticObjectId, str]

    @model_validator(mode="before")
    @classmethod
    def extract_links(cls, data: Any) -> Any:
        if isinstance(data, dict): return data
        result = {f: getattr(data, f) for f in cls.model_fields if hasattr(data, f)}
        if hasattr(data, "id"): result["id"] = str(data.id)
        if hasattr(data, "client") and data.client:
            result["client_id"] = str(data.client.id) if hasattr(data.client, "id") else str(data.client)
        return result
