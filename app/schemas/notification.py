from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    user_id: int
    notification_type: str
    title: str = Field(..., max_length=200)
    message: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[int]
    read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationMarkRead(BaseModel):
    read: bool = True
