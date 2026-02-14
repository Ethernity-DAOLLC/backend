from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class DeFiProtocolCreate(BaseModel):
    protocol_address: str = Field(..., pattern=r'^0x[a-fA-F0-9]{40}$')
    name: str = Field(..., min_length=1, max_length=64)
    apy: int = Field(..., ge=0, le=10000)
    risk_level: int = Field(..., ge=1, le=3)

class DeFiProtocolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    apy: Optional[int] = Field(None, ge=0, le=10000)
    is_active: Optional[bool] = None
    verified: Optional[bool] = None

class DeFiProtocolResponse(BaseModel):
    id: int
    protocol_address: str
    name: str
    apy: int
    risk_level: int
    is_active: bool
    verified: bool
    total_deposited: Decimal
    added_timestamp: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True

class ProtocolWithAPY(BaseModel):
    protocol_address: str
    name: str
    apy: int
    risk_level: int
    apy_percentage: float  # Calculated field

class ProtocolStats(BaseModel):
    total_protocols: int
    active_protocols: int
    verified_protocols: int
    average_apy: int
    total_tvl: Decimal