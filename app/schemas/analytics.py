from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import date, datetime
from decimal import Decimal

class DailySnapshot(BaseModel):
    snapshot_date: date
    total_token_holders: int
    active_token_holders: int
    total_funds: int
    active_funds: int
    funds_in_retirement: int
    total_deposits_today: Decimal
    total_withdrawals_today: Decimal
    total_fees_today: Decimal
    total_tvl: Decimal
    active_proposals: int
    votes_cast_today: int

class FundPerformance(BaseModel):
    fund_address: str
    owner_address: str
    initial_deposit: Decimal
    total_deposited: Decimal
    current_balance: Decimal
    total_return: Decimal
    return_percentage: float
    days_active: int
    monthly_deposits_made: int

class UserDashboard(BaseModel):
    wallet_address: str
    has_fund: bool
    fund_address: Optional[str]
    fund_balance: Optional[Decimal]
    retirement_status: Optional[str]
    is_token_holder: bool
    token_balance: Optional[Decimal]
    has_activity_this_month: bool
    total_votes_cast: int
    proposals_created: int
    last_activity: Optional[datetime]

class SystemHealthCheck(BaseModel):
    database_healthy: bool
    blockchain_synced: bool
    last_block_processed: int
    pending_events: int
    active_funds: int
    total_tvl: Decimal
    timestamp: datetime