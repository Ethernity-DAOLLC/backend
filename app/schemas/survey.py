from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class SurveyCreate(BaseModel):
    age: str = Field(..., description="Age range: 18-24, 25-34, 35-44, 45-54, 55-64, 65+")
    trust_traditional: int = Field(..., ge=-2, le=2, description="Trust in traditional pension systems (-2 to 2)")
    blockchain_familiarity: int = Field(..., ge=-2, le=2, description="Familiarity with blockchain/crypto (-2 to 2)")
    retirement_concern: int = Field(..., ge=-2, le=2, description="Concern about retirement funds (-2 to 2)")
    has_retirement_plan: int = Field(..., ge=-2, le=2, description="Has active retirement plan (-2 to 2)")
    values_in_retirement: int = Field(..., ge=-2, le=2, description="Values transparency in retirement (-2 to 2)")
    interested_in_blockchain: int = Field(..., ge=-2, le=2, description="Interest in blockchain retirement fund (-2 to 2)")

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

    class Config:
        from_attributes = True

class FollowUpCreate(BaseModel):
    wants_more_info: bool = Field(..., description="Whether user wants more information")
    email: Optional[EmailStr] = Field(None, description="User email if they want more info")

    class Config:
        json_schema_extra = {
            "example": {
                "wants_more_info": True,
                "email": "user@example.com"
            }
        }

class FollowUpResponse(BaseModel):
    id: str
    wants_more_info: bool
    email: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SurveyStats(BaseModel):
    """Schema for survey statistics"""
    total_responses: int
    averages: dict
    age_distribution: dict
    interest_level: dict

    class Config:
        json_schema_extra = {
            "example": {
                "total_responses": 150,
                "averages": {
                    "trust_traditional": 0.5,
                    "blockchain_familiarity": 0.8,
                    "retirement_concern": 1.2,
                    "has_retirement_plan": -0.3,
                    "values_in_retirement": 1.5,
                    "interested_in_blockchain": 1.1
                },
                "age_distribution": {
                    "18-24": 25,
                    "25-34": 45,
                    "35-44": 40,
                    "45-54": 25,
                    "55-64": 10,
                    "65+": 5
                },
                "interest_level": {
                    "high_interest": 60,
                    "moderate_interest": 50,
                    "low_interest": 40
                }
            }
        }

class SurveyStats(BaseModel):
    """Schema for survey statistics"""
    total_responses: int
    averages: dict
    age_distribution: dict
    interest_level: dict

    class Config:
        json_schema_extra = {
            "example": {
                "total_responses": 150,
                "averages": {
                    "trust_traditional": 0.5,
                    "blockchain_familiarity": 0.8,
                    "retirement_concern": 1.2,
                    "has_retirement_plan": -0.3,
                    "values_in_retirement": 1.5,
                    "interested_in_blockchain": 1.1
                },
                "age_distribution": {
                    "18-24": 25,
                    "25-34": 45,
                    "35-44": 40,
                    "45-54": 25,
                    "55-64": 10,
                    "65+": 5
                },
                "interest_level": {
                    "high_interest": 60,
                    "moderate_interest": 50,
                    "low_interest": 40
                }
            }
        }