from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import logging

from app.api.v1.deps import get_db
from app.schemas.survey import (
    SurveyCreate, 
    SurveyResponse, 
    FollowUpCreate, 
    FollowUpResponse,
    SurveyStats
)
router = APIRouter()
logger = logging.getLogger(__name__)

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.db.base_class import Base

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    age = Column(String(10), nullable=False)
    trust_traditional = Column(Integer, nullable=False)
    blockchain_familiarity = Column(Integer, nullable=False)
    retirement_concern = Column(Integer, nullable=False)
    has_retirement_plan = Column(Integer, nullable=False)
    values_in_retirement = Column(Integer, nullable=False)
    interested_in_blockchain = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class SurveyFollowUp(Base):
    __tablename__ = "survey_follow_ups"
    id = Column(Integer, primary_key=True, index=True)
    wants_more_info = Column(Boolean, nullable=False)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

@router.post("/", response_model=SurveyResponse, status_code=status.HTTP_201_CREATED)
async def create_survey(
    survey: SurveyCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        db_survey = Survey(
            age=survey.age,
            trust_traditional=survey.trust_traditional,
            blockchain_familiarity=survey.blockchain_familiarity,
            retirement_concern=survey.retirement_concern,
            has_retirement_plan=survey.has_retirement_plan,
            values_in_retirement=survey.values_in_retirement,
            interested_in_blockchain=survey.interested_in_blockchain,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(db_survey)
        db.commit()
        db.refresh(db_survey)
        logger.info(f"✅ Survey created: {db_survey.id}")
        return db_survey
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Survey error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating survey: {str(e)}"
        )

@router.post("/follow-up", response_model=FollowUpResponse, status_code=status.HTTP_201_CREATED)
async def create_follow_up(
    follow_up: FollowUpCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        db_follow_up = SurveyFollowUp(
            wants_more_info=follow_up.wants_more_info,
            email=follow_up.email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        db.add(db_follow_up)
        db.commit()
        db.refresh(db_follow_up)
        logger.info(f"✅ Follow-up created: {db_follow_up.id}")
        if follow_up.wants_more_info and follow_up.email:
            logger.info(f"📧 User opted in: {follow_up.email}")
        return db_follow_up
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Follow-up error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating follow-up: {str(e)}"
        )

@router.get("/", response_model=List[SurveyResponse])
async def get_surveys(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    try:
        surveys = db.query(Survey)\
            .order_by(Survey.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        logger.info(f"📊 Retrieved {len(surveys)} surveys")
        return surveys
        
    except Exception as e:
        logger.error(f"❌ Get surveys error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching surveys: {str(e)}"
        )
@router.get("/stats", response_model=SurveyStats)
async def get_survey_stats(db: Session = Depends(get_db)):
    try:
        total = db.query(Survey).count()
        if total == 0:
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
        
        averages = {
            "trust_traditional": db.query(func.avg(Survey.trust_traditional)).scalar() or 0,
            "blockchain_familiarity": db.query(func.avg(Survey.blockchain_familiarity)).scalar() or 0,
            "retirement_concern": db.query(func.avg(Survey.retirement_concern)).scalar() or 0,
            "has_retirement_plan": db.query(func.avg(Survey.has_retirement_plan)).scalar() or 0,
            "values_in_retirement": db.query(func.avg(Survey.values_in_retirement)).scalar() or 0,
            "interested_in_blockchain": db.query(func.avg(Survey.interested_in_blockchain)).scalar() or 0,
        }
        averages = {k: round(float(v), 2) for k, v in averages.items()}
        age_dist = db.query(
            Survey.age,
            func.count(Survey.id).label('count')
        ).group_by(Survey.age).all()
        age_distribution = {age: count for age, count in age_dist}
        high = db.query(Survey).filter(Survey.interested_in_blockchain >= 1).count()
        moderate = db.query(Survey).filter(Survey.interested_in_blockchain == 0).count()
        low = db.query(Survey).filter(Survey.interested_in_blockchain < 0).count()
        logger.info(f"📈 Stats for {total} surveys")
        
        return {
            "total_responses": total,
            "averages": averages,
            "age_distribution": age_distribution,
            "interest_level": {
                "high_interest": high,
                "moderate_interest": moderate,
                "low_interest": low
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating stats: {str(e)}"
        )


@router.get("/follow-ups", response_model=List[FollowUpResponse])
async def get_follow_ups(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    try:
        follow_ups = db.query(SurveyFollowUp)\
            .order_by(SurveyFollowUp.created_at.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        logger.info(f"📋 Retrieved {len(follow_ups)} follow-ups")
        return follow_ups
        
    except Exception as e:
        logger.error(f"❌ Follow-ups error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching follow-ups: {str(e)}"
        )

@router.get("/emails")
async def get_interested_emails(db: Session = Depends(get_db)):
    try:
        follow_ups = db.query(SurveyFollowUp)\
            .filter(
                SurveyFollowUp.wants_more_info == True,
                SurveyFollowUp.email.isnot(None)
            )\
            .order_by(SurveyFollowUp.created_at.desc())\
            .all()
        emails = [
            {"email": f.email, "created_at": f.created_at.isoformat()}
            for f in follow_ups
        ]
        logger.info(f"📧 Retrieved {len(emails)} emails")
        return {
            "total": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        logger.error(f"❌ Emails error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching emails: {str(e)}"
        )