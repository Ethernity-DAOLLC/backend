from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.api.deps import get_db, get_current_admin
from app.schemas.token import (
    TokenHolderResponse,
    TokenActivityCreate,
    TokenActivityResponse,
    TokenStats
)
from app.services.token_service import token_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/holder/{wallet_address}",
    response_model=TokenHolderResponse,
    summary="Get token holder info"
)
async def get_token_holder(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    holder = token_service.get_holder(db, wallet_address)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token holder not found"
        )
    
    return holder

@router.get(
    "/holder/{wallet_address}/activities",
    response_model=List[TokenActivityResponse],
    summary="Get token holder activities"
)
async def get_holder_activities(
    wallet_address: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return token_service.get_holder_activities(
        db=db,
        wallet_address=wallet_address,
        skip=skip,
        limit=limit
    )

@router.post(
    "/activity",
    response_model=TokenActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record token activity"
)
async def record_activity(
    wallet_address: str,
    activity: TokenActivityCreate,
    db: Session = Depends(get_db)
):
    try:
        return token_service.record_activity(
            db=db,
            wallet_address=wallet_address,
            activity=activity
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/stats",
    response_model=TokenStats,
    summary="Get token statistics"
)
async def get_token_stats(db: Session = Depends(get_db)):
    return token_service.get_stats(db)


@router.get(
    "/holders",
    response_model=List[TokenHolderResponse],
    summary="Get all token holders (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_all_holders(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    return token_service.get_all_holders(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only
    )

@router.get(
    "/holders/inactive",
    response_model=List[TokenHolderResponse],
    summary="Get inactive holders (no activity this month)"
)
async def get_inactive_holders(
    db: Session = Depends(get_db)
):
    return token_service.get_inactive_holders(db)

@router.get(
    "/burn/upcoming",
    summary="Get upcoming burn info"
)
async def get_burn_info(db: Session = Depends(get_db)):
    return token_service.get_burn_info(db)

@router.get(
    "/renew/upcoming",
    summary="Get upcoming renew info"
)
async def get_renew_info(db: Session = Depends(get_db)):
    return token_service.get_renew_info(db)

@router.post(
    "/sync-from-blockchain",
    summary="Sync token data from blockchain (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def sync_token_data(db: Session = Depends(get_db)):
    try:
        result = token_service.sync_from_blockchain(db)
        return result
    except Exception as e:
        logger.error(f"Error syncing token data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error syncing token data"
        )