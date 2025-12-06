from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    wallet_address: str = Field(..., min_length=42, max_length=42, pattern="^0x[a-fA-F0-9]{40}$")
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    username: Optional[str] = None
    full_name: Optional[str] = None
    accepts_marketing: bool = False
    accepts_notifications: bool = True
    preferred_language: str = "en"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    accepts_marketing: Optional[bool] = None
    accepts_notifications: Optional[bool] = None
    preferred_language: Optional[str] = None

class UserResponse(UserBase):
    id: int
    username: Optional[str]
    full_name: Optional[str]
    email_verified: bool
    accepts_marketing: bool
    accepts_notifications: bool
    preferred_language: str
    registration_date: datetime
    last_login: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class UserAdmin(UserResponse):
    last_email_sent: Optional[datetime]
    is_banned: bool
    ip_address: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class EmailAssociation(BaseModel):
    address: str = Field(..., min_length=42, max_length=42)
    email: EmailStr
    accepts_marketing: bool = False
    accepts_notifications: bool = True