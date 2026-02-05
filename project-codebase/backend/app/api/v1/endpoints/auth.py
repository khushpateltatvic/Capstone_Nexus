"""
Authentication API Endpoints

Provides:
- Login (OAuth2 token generation)
- Register (secured with admin secret)
- Current user profile
- Password reset and change
"""

from datetime import timedelta, datetime
from typing import Any, Optional
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core import security
from app.core.config import settings
from app.core.database import get_database
from app.models.domain.user import (
    User, UserCreate, UserUpdate, UserResponse,
    PasswordResetRequest, PasswordResetConfirm, PasswordChange
)
from app.models.domain.document_references import InternalStakeholder
from app.services.access_control import access_control

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependency for retrieving the current authenticated user from JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = await get_database()
    user_doc = await db.users.find_one({"email": email})
    if user_doc is None:
        raise credentials_exception
    return User(**user_doc)


@router.post("/login/access-token")
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """Standard OAuth2 token generation login."""
    db = await get_database()
    user_doc = await db.users.find_one({"email": form_data.username})
    if not user_doc or not security.verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=400, detail="User account is deactivated")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Get permissions
    permissions = []
    try:
        stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == user_doc["email"])
        if stakeholder:
            user_perms = await access_control.get_user_permissions(stakeholder)
            permissions = list(user_perms)
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        
    user_response = UserResponse(**user_doc)
    user_response.permissions = permissions
    
    return {
        "access_token": security.create_access_token(
            subject=user_doc["email"], expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "user": user_response.dict()
    }


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: UserCreate, 
    x_admin_secret: Optional[str] = Header(None)
) -> Any:
    """
    Secure Production Registration.
    Requires an 'X-Admin-Secret' header matching the server's SECRET_KEY.
    """
    if x_admin_secret != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized registration attempt.")

    db = await get_database()
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Securely hash password using bcrypt
    user_data = user_in.dict(exclude={"password"})
    user_data["hashed_password"] = security.get_password_hash(user_in.password)
    user_data["is_active"] = True
    user_data["is_superuser"] = False
    user_data["created_at"] = datetime.utcnow()

    await db.users.insert_one(user_data)
    return UserResponse(**user_data)


@router.get("/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)) -> Any:
    """Retrieves the current authenticated user profile."""
    # Get permissions
    permissions = []
    try:
        stakeholder = await InternalStakeholder.find_one(InternalStakeholder.email == current_user.email)
        if stakeholder:
            user_perms = await access_control.get_user_permissions(stakeholder)
            permissions = list(user_perms)
    except Exception as e:
        print(f"Error fetching permissions: {e}")
        
    response = UserResponse(**current_user.dict())
    response.permissions = permissions
    return response


@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update current user's profile (non-sensitive fields only)."""
    db = await get_database()
    
    # Only allow updating certain fields
    update_data = {}
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.location is not None:
        update_data["location"] = user_update.location
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    await db.users.update_one(
        {"email": current_user.email},
        {"$set": update_data}
    )
    
    updated_doc = await db.users.find_one({"email": current_user.email})
    return UserResponse(**updated_doc)


@router.post("/change-password")
async def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Change password for authenticated user."""
    if not security.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    db = await get_database()
    new_hash = security.get_password_hash(payload.new_password)
    
    await db.users.update_one(
        {"email": current_user.email},
        {"$set": {"hashed_password": new_hash}}
    )
    
    return {"status": "success", "message": "Password changed successfully"}


@router.post("/forgot-password")
async def request_password_reset(payload: PasswordResetRequest) -> Any:
    """
    Request a password reset via OTP.
    Sends a 6-digit OTP to the user's email.
    """
    from app.services.notifications.email import send_otp_email
    
    db = await get_database()
    user_doc = await db.users.find_one({"email": payload.email})
    
    if not user_doc:
        # Return success to prevent enumeration
        return {"status": "success", "message": "If the email exists, an OTP has been sent"}
    
    # Generate 6-digit OTP
    otp = "".join([secrets.choice("0123456789") for _ in range(6)])
    otp_hash = security.get_password_hash(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Update User document with OTP
    await db.users.update_one(
        {"email": payload.email},
        {
            "$set": {
                "otp_code": otp_hash,
                "otp_expires_at": expires_at
            }
        }
    )
    
    # Send Email
    # In a real async worker/queue scenario, this should be backgrounded.
    # For now, we call it directly (blocking but fast enough for SMTP usually)
    send_otp_email(payload.email, otp)
    
    return {
        "status": "success", 
        "message": "OTP sent to your email"
    }


@router.post("/reset-password")
async def confirm_password_reset(payload: PasswordResetConfirm) -> Any:
    """
    Reset password using Email + OTP + New Password.
    """
    db = await get_database()
    user_doc = await db.users.find_one({"email": payload.email})
    
    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid request")
        
    stored_otp_hash = user_doc.get("otp_code")
    expires_at = user_doc.get("otp_expires_at")
    
    if not stored_otp_hash or not expires_at:
        raise HTTPException(status_code=400, detail="No password reset requested")
        
    if datetime.utcnow() > expires_at:
        raise HTTPException(status_code=400, detail="OTP has expired")
        
    if not security.verify_password(payload.otp, stored_otp_hash):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Update password and clear OTP
    new_hash = security.get_password_hash(payload.new_password)
    
    await db.users.update_one(
        {"email": payload.email},
        {
            "$set": {
                "hashed_password": new_hash,
                "otp_code": None,
                "otp_expires_at": None
            }
        }
    )
    
    return {"status": "success", "message": "Password reset successfully"}


@router.get("/users", response_model=list)
async def list_users(
    current_user: User = Depends(get_current_user),
    x_admin_secret: Optional[str] = Header(None)
) -> Any:
    """List all users (admin only)."""
    from app.models.domain.user import UserRole
    from app.core.rbac import is_admin_role
    
    if not is_admin_role(current_user) and x_admin_secret != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = await get_database()
    users = []
    async for doc in db.users.find():
        users.append(UserResponse(**doc).dict())
    
    return users


@router.get("/users/{email}", response_model=UserResponse)
async def get_user(
    email: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user by email."""
    from app.core.rbac import is_admin_role
    
    # Users can view their own profile, admins can view anyone
    if email != current_user.email and not is_admin_role(current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    db = await get_database()
    user_doc = await db.users.find_one({"email": email})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user_doc)


@router.put("/users/{email}", response_model=UserResponse)
async def update_user(
    email: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    x_admin_secret: Optional[str] = Header(None)
) -> Any:
    """Update user (admin only can update role/department)."""
    from app.core.rbac import is_admin_role
    
    if not is_admin_role(current_user) and x_admin_secret != settings.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db = await get_database()
    user_doc = await db.users.find_one({"email": email})
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in user_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Convert role enum to string if present
    if "role" in update_data and update_data["role"]:
        update_data["role"] = update_data["role"].value
    
    await db.users.update_one(
        {"email": email},
        {"$set": update_data}
    )
    
    updated_doc = await db.users.find_one({"email": email})
    return UserResponse(**updated_doc)
