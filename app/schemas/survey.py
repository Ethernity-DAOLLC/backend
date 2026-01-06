from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class SurveyCreate(BaseModel):
    age: str = Field(..., description="Age range: 18-24, 25-34, etc.")
    trust_traditional: int = Field(..., ge=-2, le=2)
    blockchain_familiarity: int = Field(..., ge=-2, le=2)
    retirement_concern: int = Field(..., ge=-2, le=2)
    has_retirement_plan: int = Field(..., ge=-2, le=2)
    values_in_retirement: int = Field(..., ge=-2, le=2)
    interested_in_blockchain: int = Field(..., ge=-2, le=2)

class SurveyResponse(BaseModel):
    id: str
    age: str
    trust_traditional: int
    blockchain_familiarity: int
    retirement_concern: int
    has_retirement_plan: int
    values_in_retirement: int
    interested_in_blockchain: int
    created_at: datetime

class FollowUpCreate(BaseModel):
    wants_more_info: bool
    email: Optional[EmailStr] = None

class FollowUpResponse(BaseModel):
    id: str
    wants_more_info: bool
    email: Optional[str]
    created_at: datetime