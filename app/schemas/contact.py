from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=500)
    message: str = Field(..., min_length=10)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v.strip()
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "subject": "Consulta sobre el fondo de retiro",
                "message": "Hola, me gustaría saber más información sobre cómo funciona el fondo de retiro..."
            }
        }

class ContactUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    subject: Optional[str] = Field(None, min_length=5, max_length=500)
    message: Optional[str] = Field(None, min_length=10)
    is_read: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_read": True
            }
        }

class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    timestamp: datetime
    is_read: bool
    
    class Config:
        from_attributes = True

class ContactAdmin(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    timestamp: datetime
    is_read: bool
    read_at: Optional[datetime]
    ip_address: Optional[str]
    user_agent: Optional[str]
    
    class Config:
        from_attributes = True

class ContactMarkRead(BaseModel):
    is_read: bool

class ContactStats(BaseModel):
    total_messages: int
    unread_messages: int
    messages_last_7_days: int
    read_percentage: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_messages": 150,
                "unread_messages": 23,
                "messages_last_7_days": 12,
                "read_percentage": 84.67
            }
        }