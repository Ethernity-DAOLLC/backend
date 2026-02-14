from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Any, Dict, Optional
import logging

from app.models.survey import Survey, SurveyFollowUp
from app.schemas.survey import SurveyCreate, FollowUpCreate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class SurveyService(BaseService[Survey]):
    def __init__(self):
        super().__init__(Survey)

    def create_survey(
        self,
        db: Session,
        survey_in: SurveyCreate,
        client_info: dict | None = None
    ) -> Survey:
        survey_data = survey_in.model_dump()

        survey = Survey(**survey_data)
        db.add(survey)
        db.commit()
        db.refresh(survey)

        if client_info:
            logger.info(
                "Survey submitted",
                extra={
                    "survey_id": survey.id,
                    "ip": client_info.get("ip_address"),
                    "forwarded_for": client_info.get("forwarded_for"),
                }
            )

        return survey

    def get_all_surveys(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Survey]:
        return (
            db.query(Survey)
            .order_by(desc(Survey.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_stats(self, db: Session) -> dict:
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

        age_dist = (
            db.query(Survey.age, func.count(Survey.id))
            .group_by(Survey.age)
            .all()
        )

        age_distribution = {age: count for age, count in age_dist}

        high = db.query(Survey).filter(Survey.interested_in_blockchain >= 1).count()
        moderate = db.query(Survey).filter(Survey.interested_in_blockchain == 0).count()
        low = db.query(Survey).filter(Survey.interested_in_blockchain < 0).count()

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


class FollowUpService(BaseService[SurveyFollowUp]):
    def __init__(self):
        super().__init__(SurveyFollowUp)

    def create_follow_up(
        self,
        db: Session,
        follow_up_in: FollowUpCreate,
        client_info: dict | None = None
    ) -> SurveyFollowUp:
        follow_up_data = follow_up_in.model_dump()

        follow_up = SurveyFollowUp(**follow_up_data)
        db.add(follow_up)
        db.commit()
        db.refresh(follow_up)

        if client_info:
            logger.info(
                "Survey follow-up submitted",
                extra={
                    "follow_up_id": follow_up.id,
                    "ip": client_info.get("ip_address"),
                    "forwarded_for": client_info.get("forwarded_for"),
                }
            )

        return follow_up

survey_service = SurveyService()
follow_up_service = FollowUpService()
