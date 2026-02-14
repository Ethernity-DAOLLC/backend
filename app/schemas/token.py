from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class TokenHolderResponse(BaseModel):
    id: int
    wallet_address: str
    balance: Decimal
    is_active: bool
    has_activity_this_month: bool
    last_activity_timestamp: Optional[datetime]
    last_activity_type: Optional[str]
    total_burns: int
    total_renews: int
    holder_since: datetime
    
    class Config:
        from_attributes = True

class TokenActivityCreate(BaseModel):
    activity_type: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = None
    transaction_hash: Optional[str] = Field(None, pattern=r'^0x[a-fA-F0-9]{64}$')

class TokenActivityResponse(BaseModel):
    id: int
    wallet_address: str
    activity_type: str
    description: Optional[str]
    transaction_hash: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenStats(BaseModel):
    total_holders: int
    active_holders: int
    total_supply: Decimal
    current_month_burns: int
    current_month_renews: int