from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class UserPreferenceCreate(BaseModel):
    selected_protocol_id: Optional[int] = None
    auto_compound: bool = True
    risk_tolerance: int = Field(default=2, ge=1, le=3)
    strategy_type: int = Field(default=0, ge=0, le=3)
    diversification_percent: int = Field(default=0, ge=0, le=100)
    rebalance_threshold: int = Field(default=0, ge=0, le=1000)

class UserPreferenceUpdate(BaseModel):
    selected_protocol_id: Optional[int] = None
    auto_compound: Optional[bool] = None
    risk_tolerance: Optional[int] = Field(None, ge=1, le=3)
    strategy_type: Optional[int] = Field(None, ge=0, le=3)
    diversification_percent: Optional[int] = Field(None, ge=0, le=100)
    rebalance_threshold: Optional[int] = Field(None, ge=0, le=1000)

class UserPreferenceResponse(BaseModel):
    id: int
    user_id: int
    wallet_address: str
    selected_protocol_id: Optional[int]
    auto_compound: bool
    risk_tolerance: int
    strategy_type: int
    total_deposited: Decimal
    total_withdrawn: Decimal
    last_update: datetime
    
    class Config:
        from_attributes = True

class StrategyRecommendation(BaseModel):
    recommended_protocol_id: int
    protocol_name: str
    protocol_address: str
    apy: int
    risk_level: int
    reason: str