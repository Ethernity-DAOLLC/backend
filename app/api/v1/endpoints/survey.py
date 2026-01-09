from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db, get_client_info
from app.models.survey import Survey, SurveyFollowUp
from app.schemas.survey import (
    SurveyCreate, 
    SurveyResponse, 
    FollowUpCreate, 
    FollowUpResponse,
    SurveyStats
)
from app.services.survey_service import survey_service, follow_up_service
router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=SurveyResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_survey(
    survey: SurveyCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        client_info = get_client_info(request)
        db_survey = survey_service.create_survey(db, survey, client_info)
        return db_survey
        
    except Exception as e:
        logger.error(f"Survey error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating survey: {str(e)}"
        )

@router.post(
    "/follow-up",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_follow_up(
    follow_up: FollowUpCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        client_info = get_client_info(request)
        db_follow_up = follow_up_service.create_follow_up(db, follow_up, client_info)
        if follow_up.wants_more_info and follow_up.email:
            logger.info(f"📧 User opted in: {follow_up.email}")
        
        return db_follow_up
        
    except Exception as e:
        logger.error(f"Follow-up error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating follow-up: {str(e)}"
        )

@router.get(
    "/",
    response_model=List[SurveyResponse]
)
async def get_surveys(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    return survey_service.get_all_surveys(db, offset, limit)

@router.get(
    "/stats",
    response_model=SurveyStats
)
async def get_survey_stats(db: Session = Depends(get_db)):
    return survey_service.get_stats(db)

@router.get(
    "/follow-ups",
    response_model=List[FollowUpResponse]
)
async def get_follow_ups(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    return follow_up_service.get_all_follow_ups(db, offset, limit)

@router.get("/emails")
async def get_interested_emails(db: Session = Depends(get_db)):
    emails = follow_up_service.get_interested_emails(db)
    
    return {
        "total": len(emails),
        "emails": emails
    }
