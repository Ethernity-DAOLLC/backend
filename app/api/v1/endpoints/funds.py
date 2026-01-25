from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_admin, get_client_info
from app.schemas.fund import (
    PersonalFundCreate,
    PersonalFundResponse,
    FundBalances,
    FundStats,
    AutoWithdrawalConfig,
    AutoWithdrawalInfo
)
from app.services.fund_service import fund_service

router = APIRouter()
logger = logging.getLogger(__name__)
@router.post(
    "/create",
    response_model=PersonalFundResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create personal retirement fund"
)
async def create_fund(
    fund_data: PersonalFundCreate,
    wallet_address: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    try:
        client_info = get_client_info(request)
        fund = fund_service.create_fund(
            db=db,
            wallet_address=wallet_address,
            fund_data=fund_data,
            client_info=client_info
        )

        background_tasks.add_task(
            fund_service.monitor_fund_creation,
            fund.id,
            wallet_address
        )
        return fund
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating fund: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating fund"
        )

@router.get(
    "/wallet/{wallet_address}",
    response_model=PersonalFundResponse,
    summary="Get fund by wallet address"
)
async def get_fund_by_wallet(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    fund = fund_service.get_by_wallet(db, wallet_address)
    
    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found for this wallet"
        )
    return fund

@router.get(
    "/address/{fund_address}",
    response_model=PersonalFundResponse,
    summary="Get fund by contract address"
)
async def get_fund_by_address(
    fund_address: str,
    db: Session = Depends(get_db)
):
    fund = fund_service.get_by_address(db, fund_address)
    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return fund

@router.get(
    "/{fund_id}/balances",
    response_model=FundBalances,
    summary="Get fund balances"
)
async def get_fund_balances(
    fund_id: int,
    db: Session = Depends(get_db)
):
    balances = fund_service.get_balances(db, fund_id)
    if not balances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return balances

@router.get(
    "/{fund_id}/stats",
    response_model=FundStats,
    summary="Get fund statistics"
)
async def get_fund_stats(
    fund_id: int,
    db: Session = Depends(get_db)
):
    stats = fund_service.get_stats(db, fund_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return stats

@router.post(
    "/{fund_id}/deposit",
    summary="Record deposit to fund"
)
async def record_deposit(
    fund_id: int,
    transaction_hash: str,
    db: Session = Depends(get_db)
):

    try:
        result = fund_service.record_deposit(
            db=db,
            fund_id=fund_id,
            transaction_hash=transaction_hash
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/{fund_id}/withdraw",
    summary="Record withdrawal from fund"
)
async def record_withdrawal(
    fund_id: int,
    transaction_hash: str,
    db: Session = Depends(get_db)
):

    try:
        result = fund_service.record_withdrawal(
            db=db,
            fund_id=fund_id,
            transaction_hash=transaction_hash
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/{fund_id}/start-retirement",
    summary="Start retirement phase"
)
async def start_retirement(
    fund_id: int,
    transaction_hash: str,
    db: Session = Depends(get_db)
):
    try:
        result = fund_service.start_retirement(
            db=db,
            fund_id=fund_id,
            transaction_hash=transaction_hash
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{fund_id}/can-retire",
    summary="Check if fund can start retirement"
)
async def can_retire(
    fund_id: int,
    db: Session = Depends(get_db)
):
    result = fund_service.can_start_retirement(db, fund_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return result

@router.post(
    "/{fund_id}/auto-withdrawal/configure",
    summary="Configure auto-withdrawal"
)
async def configure_auto_withdrawal(
    fund_id: int,
    config: AutoWithdrawalConfig,
    db: Session = Depends(get_db)
):
    try:
        result = fund_service.configure_auto_withdrawal(
            db=db,
            fund_id=fund_id,
            config=config
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{fund_id}/auto-withdrawal",
    response_model=AutoWithdrawalInfo,
    summary="Get auto-withdrawal info"
)
async def get_auto_withdrawal_info(
    fund_id: int,
    db: Session = Depends(get_db)
):
    info = fund_service.get_auto_withdrawal_info(db, fund_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fund not found"
        )
    return info

@router.get(
    "/",
    response_model=List[PersonalFundResponse],
    summary="Get all funds (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def get_all_funds(
    skip: int = 0,
    limit: int = 100,
    retirement_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return fund_service.get_all_funds(
        db=db,
        skip=skip,
        limit=limit,
        retirement_status=retirement_status
    )

@router.get(
    "/pending-retirement",
    response_model=List[PersonalFundResponse],
    summary="Get funds ready for retirement"
)
async def get_pending_retirement(
    db: Session = Depends(get_db)
):
    return fund_service.get_funds_ready_for_retirement(db)

@router.get(
    "/in-retirement",
    response_model=List[PersonalFundResponse],
    summary="Get funds in retirement phase"
)
async def get_in_retirement(
    db: Session = Depends(get_db)
):
    return fund_service.get_funds_in_retirement(db)