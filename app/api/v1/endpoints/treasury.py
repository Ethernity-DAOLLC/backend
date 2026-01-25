from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_admin
from app.schemas.protocol import (
    DeFiProtocolCreate,
    DeFiProtocolUpdate,
    DeFiProtocolResponse,
    ProtocolWithAPY,
    ProtocolStats
)
from app.services.protocol_service import protocol_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/",
    response_model=DeFiProtocolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add DeFi protocol (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def add_protocol(
    protocol_data: DeFiProtocolCreate,
    db: Session = Depends(get_db)
):
    try:
        protocol = protocol_service.add_protocol(db, protocol_data)
        return protocol
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/",
    response_model=List[DeFiProtocolResponse],
    summary="Get all protocols"
)
async def get_protocols(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    verified_only: bool = False,
    risk_level: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return protocol_service.get_protocols(
        db=db,
        skip=skip,
        limit=limit,
        active_only=active_only,
        verified_only=verified_only,
        risk_level=risk_level
    )

@router.get(
    "/{protocol_id}",
    response_model=DeFiProtocolResponse,
    summary="Get protocol by ID"
)
async def get_protocol(
    protocol_id: int,
    db: Session = Depends(get_db)
):
    protocol = protocol_service.get_protocol(db, protocol_id)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )
    return protocol

@router.get(
    "/address/{protocol_address}",
    response_model=DeFiProtocolResponse,
    summary="Get protocol by address"
)
async def get_protocol_by_address(
    protocol_address: str,
    db: Session = Depends(get_db)
):
    protocol = protocol_service.get_by_address(db, protocol_address)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )
    return protocol

@router.patch(
    "/{protocol_id}",
    response_model=DeFiProtocolResponse,
    summary="Update protocol (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def update_protocol(
    protocol_id: int,
    update_data: DeFiProtocolUpdate,
    db: Session = Depends(get_db)
):
    try:
        protocol = protocol_service.update_protocol(db, protocol_id, update_data)
        if not protocol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Protocol not found"
            )
        return protocol
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/{protocol_id}/verify",
    response_model=DeFiProtocolResponse,
    summary="Verify protocol (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def verify_protocol(
    protocol_id: int,
    db: Session = Depends(get_db)
):
    protocol = protocol_service.verify_protocol(db, protocol_id)
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )
    return protocol

@router.post(
    "/{protocol_id}/toggle-status",
    response_model=DeFiProtocolResponse,
    summary="Toggle protocol active status (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def toggle_protocol_status(
    protocol_id: int,
    db: Session = Depends(get_db)
):
    protocol = protocol_service.toggle_status(db, protocol_id)
    
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocol not found"
        )
    return protocol

@router.get(
    "/best-apy",
    response_model=List[ProtocolWithAPY],
    summary="Get protocols sorted by APY"
)
async def get_best_apy_protocols(
    risk_level: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return protocol_service.get_best_apy(
        db=db,
        risk_level=risk_level,
        limit=limit
    )

@router.get(
    "/by-risk/{risk_level}",
    response_model=List[DeFiProtocolResponse],
    summary="Get protocols by risk level"
)
async def get_protocols_by_risk(
    risk_level: int,
    db: Session = Depends(get_db)
):
    if risk_level not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Risk level must be 1 (LOW), 2 (MEDIUM), or 3 (HIGH)"
        )
    return protocol_service.get_by_risk_level(db, risk_level)

@router.get(
    "/stats",
    response_model=ProtocolStats,
    summary="Get protocol statistics"
)
async def get_protocol_stats(db: Session = Depends(get_db)):
    return protocol_service.get_stats(db)

@router.post(
    "/{protocol_id}/update-apy",
    summary="Update protocol APY (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def update_protocol_apy(
    protocol_id: int,
    new_apy: int,
    db: Session = Depends(get_db)
):
    try:
        result = protocol_service.update_apy(db, protocol_id, new_apy)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{protocol_id}/apy-history",
    summary="Get APY history for protocol"
)
async def get_apy_history(
    protocol_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return protocol_service.get_apy_history(db, protocol_id, limit)