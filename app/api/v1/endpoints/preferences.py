from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.api.deps import get_db
from app.schemas.preferences import (
    UserPreferenceCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    StrategyRecommendation
)
from app.services.preference_service import preference_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=UserPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user preferences"
)
async def create_preferences(
    wallet_address: str,
    preferences: UserPreferenceCreate,
    db: Session = Depends(get_db)
):
    try:
        prefs = preference_service.create_preferences(
            db=db,
            wallet_address=wallet_address,
            preferences=preferences
        )
        return prefs
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{wallet_address}",
    response_model=UserPreferenceResponse,
    summary="Get user preferences"
)
async def get_preferences(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    prefs = preference_service.get_preferences(db, wallet_address)
    if not prefs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    return prefs

@router.patch(
    "/{wallet_address}",
    response_model=UserPreferenceResponse,
    summary="Update user preferences"
)
async def update_preferences(
    wallet_address: str,
    updates: UserPreferenceUpdate,
    db: Session = Depends(get_db)
):
    try:
        prefs = preference_service.update_preferences(
            db=db,
            wallet_address=wallet_address,
            updates=updates
        )
        if not prefs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )
        return prefs
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{wallet_address}/recommendation",
    response_model=StrategyRecommendation,
    summary="Get protocol recommendation"
)
async def get_recommendation(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    recommendation = preference_service.get_recommendation(db, wallet_address)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot generate recommendation"
        )
    return recommendation
