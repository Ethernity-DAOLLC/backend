from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_admin
from app.schemas.blockchain import (
    BlockchainEventCreate,
    BlockchainEventResponse,
    EventFilter
)
from app.services.blockchain_service import blockchain_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/events",
    response_model=BlockchainEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record blockchain event"
)
async def record_event(
    event: BlockchainEventCreate,
    db: Session = Depends(get_db)
):
    try:
        return blockchain_service.record_event(db, event)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/events",
    response_model=List[BlockchainEventResponse],
    summary="Get blockchain events"
)
async def get_events(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    contract_address: Optional[str] = None,
    processed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    return blockchain_service.get_events(
        db=db,
        skip=skip,
        limit=limit,
        event_type=event_type,
        contract_address=contract_address,
        processed=processed
    )

@router.get(
    "/events/{event_id}",
    response_model=BlockchainEventResponse,
    summary="Get event by ID"
)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = blockchain_service.get_event(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

@router.get(
    "/events/tx/{transaction_hash}",
    response_model=List[BlockchainEventResponse],
    summary="Get events by transaction hash"
)
async def get_events_by_tx(
    transaction_hash: str,
    db: Session = Depends(get_db)
):
    return blockchain_service.get_events_by_tx(db, transaction_hash)

@router.post(
    "/events/{event_id}/mark-processed",
    response_model=BlockchainEventResponse,
    summary="Mark event as processed"
)
async def mark_event_processed(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = blockchain_service.mark_processed(db, event_id)
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event

@router.get(
    "/events/unprocessed",
    response_model=List[BlockchainEventResponse],
    summary="Get unprocessed events"
)
async def get_unprocessed_events(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return blockchain_service.get_unprocessed(db, limit)

@router.post(
    "/sync",
    summary="Sync blockchain data (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def sync_blockchain(
    from_block: Optional[int] = None,
    to_block: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        result = blockchain_service.sync_events(
            db=db,
            from_block=from_block,
            to_block=to_block
        )
        return result
        
    except Exception as e:
        logger.error(f"Blockchain sync error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blockchain sync failed"
        )

@router.get(
    "/sync/status",
    summary="Get sync status"
)
async def get_sync_status(db: Session = Depends(get_db)):
    return blockchain_service.get_sync_status(db)