from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.api.deps import get_db, get_current_admin
from app.services.contact_service import contact_service
from app.services.user_service import user_service
from app.services.survey_service import survey_service

router = APIRouter()

@router.get(
    "/admin/stats",
    response_model=Dict[str, Any],
    dependencies=[Depends(get_current_admin)]
)
async def get_admin_stats(db: Session = Depends(get_db)):
    return {
        "users": user_service.get_stats(db),
        "contacts": contact_service.get_stats(db),
        "surveys": survey_service.get_stats(db),
    }