from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import asyncio
import logging

from .web3_client import web3_client
from .contract_manager import contract_manager
from app.db.session import SessionLocal
from app.services.blockchain_service import blockchain_service
from app.schemas.blockchain import BlockchainEventCreate

logger = logging.getLogger(__name__)

class EventListener:
    def __init__(self):
        self.is_running = False
        self.last_processed_block = 0
        self.poll_interval = 12 
        self.batch_size = 100 
    
    async def start(self):
        if self.is_running:
            logger.warning("Event listener already running")
            return
        
        self.is_running = True
        logger.info("🎧 Starting blockchain event listener")
        db = SessionLocal()
        try:
            status = blockchain_service.get_sync_status(db)
            self.last_processed_block = status.get("last_synced_block", 0)
        finally:
            db.close()
        while self.is_running:
            try:
                await self._process_new_blocks()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in event listener: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval * 2)
    
    async def stop(self):
        logger.info("🛑 Stopping event listener")
        self.is_running = False
    
    async def _process_new_blocks(self):
        if not web3_client.is_connected():
            logger.warning("Web3 not connected, skipping")
            return
        
        current_block = web3_client.get_latest_block()
        if current_block <= self.last_processed_block:
            return

        from_block = self.last_processed_block + 1
        to_block = min(from_block + self.batch_size, current_block)
        logger.info(f"📦 Processing blocks {from_block} to {to_block}")
        await self._process_token_events(from_block, to_block)
        await self._process_factory_events(from_block, to_block)
        await self._process_governance_events(from_block, to_block)
        await self._process_fund_events(from_block, to_block)
        
        self.last_processed_block = to_block
        logger.info(f"✅ Processed up to block {to_block}")
    async def _process_token_events(self, from_block: int, to_block: int):
        contract = contract_manager.get_contract("token")
        if not contract:
            return
        
        try:
            transfer_filter = contract.events.Transfer.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            for event in transfer_filter.get_all_entries():
                await self._save_event("Transfer", "token", event)
            if hasattr(contract.events, 'TokensBurned'):
                burn_filter = contract.events.TokensBurned.create_filter(
                    fromBlock=from_block,
                    toBlock=to_block
                )
                for event in burn_filter.get_all_entries():
                    await self._save_event("TokensBurned", "token", event)
            if hasattr(contract.events, 'TokensRenewed'):
                renew_filter = contract.events.TokensRenewed.create_filter(
                    fromBlock=from_block,
                    toBlock=to_block
                )
                for event in renew_filter.get_all_entries():
                    await self._save_event("TokensRenewed", "token", event)
        except Exception as e:
            logger.error(f"Error processing token events: {e}", exc_info=True)
    
    async def _process_factory_events(self, from_block: int, to_block: int):
        contract = contract_manager.get_contract("factory")
        if not contract:
            return
        
        try:
            fund_filter = contract.events.FundCreated.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            for event in fund_filter.get_all_entries():
                await self._save_event("FundCreated", "factory", event)
        except Exception as e:
            logger.error(f"Error processing factory events: {e}", exc_info=True)
    
    async def _process_governance_events(self, from_block: int, to_block: int):
        contract = contract_manager.get_contract("governance")
        if not contract:
            return
        
        try:
            proposal_filter = contract.events.ProposalCreated.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            for event in proposal_filter.get_all_entries():
                await self._save_event("ProposalCreated", "governance", event)
            vote_filter = contract.events.VoteCast.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            for event in vote_filter.get_all_entries():
                await self._save_event("VoteCast", "governance", event)
                
        except Exception as e:
            logger.error(f"Error processing governance events: {e}", exc_info=True)
    async def _process_fund_events(self, from_block: int, to_block: int):
        pass
    async def _save_event(self, event_name: str, contract_type: str, event_data: Dict):
        db = SessionLocal()
        try:
            block = web3_client.get_block(event_data['blockNumber'])
            event_create = BlockchainEventCreate(
                event_type=event_name,
                contract_address=event_data['address'],
                event_data=dict(event_data['args']),
                transaction_hash=event_data['transactionHash'].hex(),
                block_number=event_data['blockNumber'],
                block_timestamp=datetime.fromtimestamp(block['timestamp']),
                log_index=event_data['logIndex']
            )
            blockchain_service.record_event(db, event_create)
            logger.info(f"📝 Saved event: {event_name} from {contract_type}")
        except Exception as e:
            logger.error(f"Error saving event: {e}", exc_info=True)
        finally:
            db.close()

event_listener = EventListener()