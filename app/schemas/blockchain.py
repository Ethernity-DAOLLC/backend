from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class BlockchainEventCreate(BaseModel):
    event_type: str
    contract_address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    event_data: Dict[str, Any]
    transaction_hash: str = Field(..., pattern=r'^0x[a-fA-F0-9]{64}$')
    block_number: int
    block_timestamp: datetime
    log_index: int

class BlockchainEventResponse(BaseModel):
    id: int
    event_type: str
    contract_address: str
    event_data: Dict[str, Any]
    transaction_hash: str
    block_number: int
    block_timestamp: datetime
    processed: bool
    processed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class EventFilter(BaseModel):
    event_types: Optional[List[str]] = None
    contract_address: Optional[str] = None
    from_block: Optional[int] = None
    to_block: Optional[int] = None
    processed: Optional[bool] = None
