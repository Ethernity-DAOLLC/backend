from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from app.api.deps import get_db, get_current_admin
from app.schemas.analytics import (
    DailySnapshot,
    FundPerformance,
    UserDashboard,
    SystemHealthCheck
)
from app.services.analytics_service import analytics_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/dashboard/{wallet_address}",
    response_model=UserDashboard,
    summary="Get user dashboard"
)
async def get_user_dashboard(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    dashboard = analytics_service.get_user_dashboard(db, wallet_address)
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return dashboard

@router.get(
    "/fund/{fund_id}/performance",
    response_model=FundPerformance,
    summary="Get fund performance metrics"
)
async def get_fund_performance(
    fund_id: int,
    db: Session = Depends(get_db)
):
    performance = analytics_service.get_fund_performance(db, fund_id)
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return performance

@router.get(
    "/snapshots",
    response_model=List[DailySnapshot],
    summary="Get daily snapshots (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_daily_snapshots(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    return analytics_service.get_snapshots(
        db=db,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )

@router.post(
    "/snapshots/create",
    response_model=DailySnapshot,
    summary="Create daily snapshot (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def create_daily_snapshot(db: Session = Depends(get_db)):
    try:
        snapshot = analytics_service.create_snapshot(db)
        return snapshot
        
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating snapshot"
        )

@router.get(
    "/health",
    response_model=SystemHealthCheck,
    summary="System health check"
)
async def health_check(db: Session = Depends(get_db)):
    return analytics_service.health_check(db)

@router.get(
    "/metrics/overview",
    summary="Get system metrics overview (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_metrics_overview(db: Session = Depends(get_db)):
    return analytics_service.get_system_metrics(db)

@router.get(
    "/top-funds",
    response_model=List[FundPerformance],
    summary="Get top performing funds (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_top_funds(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return analytics_service.get_top_funds(db, limit)