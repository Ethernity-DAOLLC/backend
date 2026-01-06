from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.survey import (
    SurveyCreate, 
    SurveyResponse, 
    FollowUpCreate, 
    FollowUpResponse,
    SurveyStats
)
from app.db.supabase import get_supabase_client
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/surveys", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(survey: SurveyCreate):
    try:
        supabase = get_supabase_client()
        data = {
            "age": survey.age,
            "trust_traditional": survey.trust_traditional,
            "blockchain_familiarity": survey.blockchain_familiarity,
            "retirement_concern": survey.retirement_concern,
            "has_retirement_plan": survey.has_retirement_plan,
            "values_in_retirement": survey.values_in_retirement,
            "interested_in_blockchain": survey.interested_in_blockchain
        }
        
        result = supabase.table("surveys").insert(data).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create survey"
            )
        
        logger.info(f"Survey created successfully: {result.data[0]['id']}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating survey: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating survey"
        )

@router.post("/surveys/follow-up", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def create_follow_up(follow_up: FollowUpCreate):
    try:
        supabase = get_supabase_client()
        data = {
            "wants_more_info": follow_up.wants_more_info,
            "email": follow_up.email
        }
        result = supabase.table("survey_follow_ups").insert(data).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create follow-up"
            )
        
        logger.info(f"Follow-up created successfully: {result.data[0]['id']}")
        
        # TODO: If wants_more_info is True and email is provided, 
        # trigger email notification or add to mailing list
        if follow_up.wants_more_info and follow_up.email:
            logger.info(f"User {follow_up.email} opted in for more information")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating follow-up: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating follow-up"
        )

@router.get("/surveys", response_model=List[SurveyResponse])
async def get_surveys(limit: int = 100, offset: int = 0):
    try:
        supabase = get_supabase_client()
        result = supabase.table("surveys")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        logger.info(f"Retrieved {len(result.data)} surveys")
        return result.data
        
    except Exception as e:
        logger.error(f"Error fetching surveys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching surveys"
        )

@router.get("/surveys/stats", response_model=SurveyStats)
async def get_survey_stats():
    try:
        supabase = get_supabase_client()
        surveys_result = supabase.table("surveys").select("*").execute()
        surveys = surveys_result.data
        
        if not surveys:
            return {
                "total_responses": 0,
                "averages": {},
                "age_distribution": {},
                "interest_level": {
                    "high_interest": 0,
                    "moderate_interest": 0,
                    "low_interest": 0
                }
            }
        
        total = len(surveys)
        fields = [
            "trust_traditional",
            "blockchain_familiarity", 
            "retirement_concern",
            "has_retirement_plan",
            "values_in_retirement",
            "interested_in_blockchain"
        ]
        
        averages = {}
        for field in fields:
            values = [s[field] for s in surveys if s.get(field) is not None]
            averages[field] = round(sum(values) / len(values), 2) if values else 0
        age_distribution = _get_age_distribution(surveys)
        interest_level = _calculate_interest_level(surveys)
        logger.info(f"Generated stats for {total} surveys")
        
        return {
            "total_responses": total,
            "averages": averages,
            "age_distribution": age_distribution,
            "interest_level": interest_level
        }
        
    except Exception as e:
        logger.error(f"Error fetching survey stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while calculating statistics"
        )

@router.get("/surveys/follow-ups", response_model=List[FollowUpResponse])
async def get_follow_ups(limit: int = 100, offset: int = 0):
    try:
        supabase = get_supabase_client()
        result = supabase.table("survey_follow_ups")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        logger.info(f"Retrieved {len(result.data)} follow-ups")
        return result.data
        
    except Exception as e:
        logger.error(f"Error fetching follow-ups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching follow-ups"
        )

@router.get("/surveys/emails")
async def get_interested_emails():
    try:
        supabase = get_supabase_client()
        result = supabase.table("survey_follow_ups")\
            .select("email, created_at")\
            .eq("wants_more_info", True)\
            .not_.is_("email", "null")\
            .order("created_at", desc=True)\
            .execute()
        emails = [{"email": r["email"], "created_at": r["created_at"]} for r in result.data]
        logger.info(f"Retrieved {len(emails)} interested emails")
        return {
            "total": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        logger.error(f"Error fetching interested emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching emails"
        )

def _get_age_distribution(surveys: List[dict]) -> dict:

    distribution = {}
    for survey in surveys:
        age = survey.get("age", "Unknown")
        distribution[age] = distribution.get(age, 0) + 1
    return distribution

def _calculate_interest_level(surveys: List[dict]) -> dict:
    high = 0
    moderate = 0
    low = 0
    
    for survey in surveys:
        score = survey.get("interested_in_blockchain", 0)
        if score >= 1:
            high += 1
        elif score == 0:
            moderate += 1
        else:
            low += 1
    
    return {
        "high_interest": high,
        "moderate_interest": moderate,
        "low_interest": low
    }