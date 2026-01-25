from celery import Task
from typing import Optional, Dict, Any
import logging

from .celery_app import celery_app
from app.db.session import SessionLocal
from app.services.blockchain_service import blockchain_service
from app.blockchain.web3_client import web3_client
from app.blockchain.event_listener import event_listener

logger = logging.getLogger(__name__)

class DatabaseTask(Task):
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None

@celery_app.task(base=DatabaseTask, bind=True)
def sync_blockchain_events(self):
    try:
        if not web3_client.is_connected():
            logger.warning("Web3 not connected, skipping sync")
            return {"status": "skipped", "reason": "not_connected"}
        
        latest_block = web3_client.get_latest_block()
        status = blockchain_service.get_sync_status(self.db)
        last_synced = status.get("last_synced_block", 0)
        if latest_block <= last_synced:
            return {"status": "up_to_date", "block": latest_block}
        result = blockchain_service.sync_events(
            db=self.db,
            from_block=last_synced + 1,
            to_block=latest_block
        )
        logger.info(f"📦 Synced blocks {last_synced + 1} to {latest_block}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing blockchain: {e}", exc_info=True)
        raise

@celery_app.task(base=DatabaseTask, bind=True)
def process_pending_events(self):
    try:
        unprocessed = blockchain_service.get_unprocessed(self.db, limit=50)
        if not unprocessed:
            return {"status": "no_events", "processed": 0}
        
        processed_count = 0
        for event in unprocessed:
            try:
                if event.event_type == "FundCreated":
                    _process_fund_created(self.db, event)
                elif event.event_type == "Transfer":
                    _process_token_transfer(self.db, event)
                elif event.event_type == "ProposalCreated":
                    _process_proposal_created(self.db, event)
                elif event.event_type == "VoteCast":
                    _process_vote_cast(self.db, event)
                blockchain_service.mark_processed(self.db, event.id)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}")
                continue
        
        logger.info(f"✅ Processed {processed_count} events")
        return {"status": "success", "processed": processed_count}
        
    except Exception as e:
        logger.error(f"Error processing events: {e}", exc_info=True)
        raise

@celery_app.task(base=DatabaseTask, bind=True)
def monitor_fund_creation(self, fund_id: int, wallet_address: str):
    try:
        logger.info(f"🔍 Monitoring fund creation for {wallet_address}")
        return {"status": "monitoring", "fund_id": fund_id}
        
    except Exception as e:
        logger.error(f"Error monitoring fund creation: {e}", exc_info=True)
        raise

def _process_fund_created(db, event):
    from app.services.fund_service import fund_service
    data = event.event_data
    logger.info(f"💼 Fund created: {data.get('fundAddress')}")

def _process_token_transfer(db, event):
    from app.services.token_service import token_service
    data = event.event_data
    if data.get('sender') == '0x0000000000000000000000000000000000000000':
        logger.info(f"🪙 Token minted to {data.get('receiver')}")

def _process_proposal_created(db, event):
    logger.info(f"📜 Proposal created: #{event.event_data.get('proposalId')}")

def _process_vote_cast(db, event):
    logger.info(f"🗳️ Vote cast on proposal #{event.event_data.get('proposalId')}")
