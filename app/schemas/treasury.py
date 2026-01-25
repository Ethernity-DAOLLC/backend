from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class EarlyRetirementRequestCreate(BaseModel):
    fund_address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    reason: str = Field(..., min_length=10, max_length=512)

class EarlyRetirementRequestResponse(BaseModel):
    id: int
    fund_address: str
    requester_address: str
    proposal_id: Optional[int]
    reason: str
    approved: bool
    rejected: bool
    processed: bool
    votes_for: Decimal
    votes_against: Decimal
    request_timestamp: datetime
    processed_timestamp: Optional[datetime]
    
    class Config:
        from_attributes = True

class TreasuryStatsResponse(BaseModel):
    total_fees_collected_usdc: Decimal
    total_fees_collected_all_time: Decimal
    total_fees_withdrawn: Decimal
    total_funds_registered: int
    active_funds_count: int
    total_early_retirement_requests: int
    approved_early_retirements: int
    rejected_early_retirements: int
    pending_requests_count: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FundFeeRecordResponse(BaseModel):
    fund_address: str
    total_fees_paid: Decimal
    fee_count: int
    last_fee_timestamp: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True