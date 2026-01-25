from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.models.blockchain import BlockchainEvent
from app.schemas.blockchain import BlockchainEventCreate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

class BlockchainService(BaseService[BlockchainEvent]):
    def __init__(self):
        super().__init__(BlockchainEvent)
    
    def record_event(self, db: Session, event: BlockchainEventCreate) -> BlockchainEvent:
        existing = db.query(BlockchainEvent).filter(
            BlockchainEvent.transaction_hash == event.transaction_hash,
            BlockchainEvent.log_index == event.log_index
        ).first()
        if existing:
            logger.warning(f"Duplicate event: {event.transaction_hash}:{event.log_index}")
            return existing
        
        blockchain_event = BlockchainEvent(
            event_type=event.event_type,
            contract_address=event.contract_address,
            event_data=event.event_data,
            transaction_hash=event.transaction_hash,
            block_number=event.block_number,
            block_timestamp=event.block_timestamp,
            log_index=event.log_index
        )
        
        db.add(blockchain_event)
        db.commit()
        db.refresh(blockchain_event)
        logger.info(f"📝 Event recorded: {event.event_type} at block {event.block_number}")
        return blockchain_event
    
    def get_events(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_type: Optional[str] = None,
        contract_address: Optional[str] = None,
        processed: Optional[bool] = None
    ) -> List[BlockchainEvent]:
        query = db.query(BlockchainEvent)
        if event_type:
            query = query.filter(BlockchainEvent.event_type == event_type)
        if contract_address:
            query = query.filter(BlockchainEvent.contract_address == contract_address)
        if processed is not None:
            query = query.filter(BlockchainEvent.processed == processed)
        
        return query.order_by(
            desc(BlockchainEvent.block_number)
        ).offset(skip).limit(limit).all()
    
    def get_event(self, db: Session, event_id: int) -> Optional[BlockchainEvent]:
        return self.get(db, event_id)
    
    def get_events_by_tx(self, db: Session, transaction_hash: str) -> List[BlockchainEvent]:
        return db.query(BlockchainEvent).filter(
            BlockchainEvent.transaction_hash == transaction_hash
        ).order_by(BlockchainEvent.log_index).all()
    
    def mark_processed(self, db: Session, event_id: int) -> Optional[BlockchainEvent]:
        event = self.get(db, event_id)
        if not event:
            return None
        
        event.processed = True
        event.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(event)
        return event
    
    def get_unprocessed(self, db: Session, limit: int = 100) -> List[BlockchainEvent]:
        return db.query(BlockchainEvent).filter(
            BlockchainEvent.processed == False
        ).order_by(BlockchainEvent.block_number).limit(limit).all()
    
    def sync_events(
        self,
        db: Session,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None
    ) -> Dict[str, Any]:
        logger.info(f"🔄 Syncing events from block {from_block} to {to_block}")
        return {"success": True, "message": "Sync initiated"}
    
    def get_sync_status(self, db: Session) -> Dict[str, Any]:
        last_event = db.query(BlockchainEvent).order_by(
            desc(BlockchainEvent.block_number)
        ).first()
        unprocessed = db.query(BlockchainEvent).filter(
            BlockchainEvent.processed == False
        ).count()
        
        return {
            "last_synced_block": last_event.block_number if last_event else 0,
            "last_synced_at": last_event.created_at if last_event else None,
            "unprocessed_events": unprocessed
        }

blockchain_service = BlockchainService()