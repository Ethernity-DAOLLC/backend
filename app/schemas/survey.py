from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional, Dict

class SurveyCreate(BaseModel):
    age: str = Field(..., pattern=r"^(18-24|25-34|35-44|45-54|55-64|65\+)$")
    trust_traditional: int = Field(..., ge=-2, le=2)
    blockchain_familiarity: int = Field(..., ge=-2, le=2)
    retirement_concern: int = Field(..., ge=-2, le=2)
    has_retirement_plan: int = Field(..., ge=-2, le=2)
    values_in_retirement: int = Field(..., ge=-2, le=2)
    interested_in_blockchain: int = Field(..., ge=-2, le=2)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "age": "25-34",
                "trust_traditional": 0,
                "blockchain_familiarity": 1,
                "retirement_concern": 2,
                "has_retirement_plan": -1,
                "values_in_retirement": 2,
                "interested_in_blockchain": 1
            }
        }

class FollowUpCreate(BaseModel):
    wants_more_info: bool
    email: Optional[EmailStr] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    @field_validator('email')
    @classmethod
    def validate_email_if_wants_info(cls, v, info):
        if info.data.get('wants_more_info') and not v:
            raise ValueError('Email is required when wants_more_info is True')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "wants_more_info": True,
                "email": "user@example.com"
            }
        }

class SurveyResponse(BaseModel):
    id: int
    age: str
    trust_traditional: int
    blockchain_familiarity: int
    retirement_concern: int
    has_retirement_plan: int
    values_in_retirement: int
    interested_in_blockchain: int
    created_at: datetime
    class Config:
        from_attributes = True

class FollowUpResponse(BaseModel):
    id: int
    wants_more_info: bool
    email: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class SurveyAdmin(SurveyResponse):
    ip_address: Optional[str]
    user_agent: Optional[str]
    class Config:
        from_attributes = True

class FollowUpAdmin(FollowUpResponse):
    ip_address: Optional[str]
    user_agent: Optional[str]
    class Config:
        from_attributes = True

class SurveyStats(BaseModel):
    total_responses: int
    averages: Dict[str, float]
    age_distribution: Dict[str, int]
    interest_level: Dict[str, int]
    class Config:
        json_schema_extra = {
            "example": {
                "total_responses": 150,
                "averages": {
                    "trust_traditional": 0.5,
                    "blockchain_familiarity": 1.2,
                    "retirement_concern": 1.8,
                    "has_retirement_plan": -0.3,
                    "values_in_retirement": 1.9,
                    "interested_in_blockchain": 1.5
                },
                "age_distribution": {
                    "18-24": 20,
                    "25-34": 45,
                    "35-44": 35,
                    "45-54": 30,
                    "55-64": 15,
                    "65+": 5
                },
                "interest_level": {
                    "high_interest": 80,
                    "moderate_interest": 50,
                    "low_interest": 20
                }
            }
        }