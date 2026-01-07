from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Optional
from app.models.survey import Survey, SurveyFollowUp
from app.schemas.survey import SurveyCreate, FollowUpCreate
import logging

logger = logging.getLogger(__name__)

class SurveyService:
    @staticmethod
    def create_survey(db: Session, survey: SurveyCreate) -> Survey:
        db_survey = Survey(
            age=survey.age,
            trust_traditional=survey.trust_traditional,
            blockchain_familiarity=survey.blockchain_familiarity,
            retirement_concern=survey.retirement_concern,
            has_retirement_plan=survey.has_retirement_plan,
            values_in_retirement=survey.values_in_retirement,
            interested_in_blockchain=survey.interested_in_blockchain,
            ip_address=survey.ip_address,
            user_agent=survey.user_agent
        )
        
        try:
            db.add(db_survey)
            db.commit()
            db.refresh(db_survey)
            logger.info(f"✅ Survey created: ID={db_survey.id}")
            return db_survey
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating survey: {e}")
            raise

    @staticmethod
    def create_follow_up(db: Session, follow_up: FollowUpCreate) -> SurveyFollowUp:
        db_follow_up = SurveyFollowUp(
            wants_more_info=follow_up.wants_more_info,
            email=follow_up.email,
            ip_address=follow_up.ip_address,
            user_agent=follow_up.user_agent
        )
        
        try:
            db.add(db_follow_up)
            db.commit()
            db.refresh(db_follow_up)
            
            if follow_up.wants_more_info and follow_up.email:
                logger.info(f"📧 New email for mailing list: {follow_up.email}")
            logger.info(f"✅ Follow-up created: ID={db_follow_up.id}")
            return db_follow_up
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error creating follow-up: {e}")
            raise

    @staticmethod
    def get_surveys(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Survey]:
        return db.query(Survey)\
            .order_by(Survey.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_survey_by_id(db: Session, survey_id: int) -> Optional[Survey]:
        return db.query(Survey).filter(Survey.id == survey_id).first()

    @staticmethod
    def get_follow_ups(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[SurveyFollowUp]:
        return db.query(SurveyFollowUp)\
            .order_by(SurveyFollowUp.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_interested_emails(db: Session) -> List[Dict[str, str]]:
        results = db.query(
            SurveyFollowUp.email, 
            SurveyFollowUp.created_at
        ).filter(
            SurveyFollowUp.wants_more_info == True,
            SurveyFollowUp.email.isnot(None)
        ).order_by(
            SurveyFollowUp.created_at.desc()
        ).all()
        
        return [
            {
                "email": email, 
                "created_at": created_at.isoformat()
            } 
            for email, created_at in results
        ]

    @staticmethod
    def get_survey_stats(db: Session) -> Dict:
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

        fields = [
            'trust_traditional',
            'blockchain_familiarity',
            'retirement_concern',
            'has_retirement_plan',
            'values_in_retirement',
            'interested_in_blockchain'
        ]
        
        averages = {}
        for field in fields:
            avg = db.query(func.avg(getattr(Survey, field))).scalar()
            averages[field] = round(float(avg), 2) if avg else 0.0
        age_dist = db.query(
            Survey.age, 
            func.count(Survey.id)
        ).group_by(Survey.age).all()
        
        age_distribution = {age: count for age, count in age_dist}
        high = db.query(Survey).filter(Survey.interested_in_blockchain >= 1).count()
        moderate = db.query(Survey).filter(Survey.interested_in_blockchain == 0).count()
        low = db.query(Survey).filter(Survey.interested_in_blockchain <= -1).count()

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

    @staticmethod
    def delete_survey(db: Session, survey_id: int) -> bool:
        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if survey:
            db.delete(survey)
            db.commit()
            logger.info(f"🗑️ Survey deleted: ID={survey_id}")
            return True
        return False

    @staticmethod
    def delete_follow_up(db: Session, follow_up_id: int) -> bool:
        follow_up = db.query(SurveyFollowUp).filter(
            SurveyFollowUp.id == follow_up_id
        ).first()
        if follow_up:
            db.delete(follow_up)
            db.commit()
            logger.info(f"🗑️ Follow-up deleted: ID={follow_up_id}")
            return True
        return False