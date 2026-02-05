from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Role hierarchy for RBAC - higher roles have more permissions"""
    TRAINEE = "trainee"
    ANALYST = "analyst"
    LEAD = "lead"
    HEAD = "head"
    ADMIN = "admin"
    DIRECTOR = "director"


# Role hierarchy for permission checking (index = privilege level)
ROLE_HIERARCHY = [
    UserRole.TRAINEE,
    UserRole.ANALYST,
    UserRole.LEAD,
    UserRole.HEAD,
    UserRole.ADMIN,
    UserRole.DIRECTOR,
]


def get_role_level(role: UserRole) -> int:
    """Get numeric level for role comparison"""
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return 0


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    employee_number: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    role: UserRole = UserRole.TRAINEE
    manager_email: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    role: Optional[UserRole] = None
    manager_email: Optional[str] = None
    is_active: Optional[bool] = None


class User(BaseModel):
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    employee_number: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    role: UserRole = UserRole.TRAINEE
    reportees_count: int = 0
    manager_email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    otp_code: Optional[str] = None
    otp_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    

class UserResponse(BaseModel):
    """User response without sensitive fields"""
    email: EmailStr
    full_name: Optional[str] = None
    employee_number: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    role: UserRole = UserRole.TRAINEE
    reportees_count: int = 0
    manager_email: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    permissions: List[str] = []


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
