from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class PersonalFundCreate(BaseModel):
    principal: Decimal = Field(..., ge=0, decimal_places=6)
    monthly_deposit: Decimal = Field(..., gt=0, decimal_places=6)
    current_age: int = Field(..., ge=18, le=80)
    retirement_age: int = Field(..., ge=55, le=100)
    desired_monthly: Decimal = Field(..., gt=0, decimal_places=6)
    years_payments: int = Field(..., ge=1, le=50)
    interest_rate: int = Field(..., ge=0, le=10000)
    timelock_years: int = Field(default=15, ge=10, le=50)
    @field_validator('retirement_age')
    @classmethod
    def validate_retirement_age(cls, v, info):
        if 'current_age' in info.data and v <= info.data['current_age']:
            raise ValueError('Retirement age must be greater than current age')
        return v

class PersonalFundResponse(BaseModel):
    id: int
    fund_address: str
    owner_address: str
    principal: Decimal
    monthly_deposit: Decimal
    retirement_age: int
    total_balance: Decimal
    available_balance: Decimal
    total_invested: Decimal
    total_withdrawn: Decimal
    retirement_started: bool
    early_retirement_approved: bool
    timelock_end: datetime
    monthly_deposit_count: int
    withdrawal_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class FundBalances(BaseModel):
    total_balance: Decimal
    available_balance: Decimal
    total_invested: Decimal
    total_gross_deposited: Decimal
    total_fees_paid: Decimal
    total_withdrawn: Decimal

class FundStats(BaseModel):
    total_deposits: int
    total_withdrawals: int
    average_deposit: Decimal
    total_fees_paid: Decimal
    investment_count: int

class AutoWithdrawalConfig(BaseModel):
    enabled: bool
    amount: Decimal = Field(..., ge=0)
    interval_days: int = Field(..., ge=7)

class AutoWithdrawalInfo(BaseModel):
    enabled: bool
    amount: Decimal
    interval: int
    next_execution_time: Optional[datetime]
    execution_count: int
    last_execution_time: Optional[datetime]