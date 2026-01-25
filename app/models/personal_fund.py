from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class PersonalFund(Base):
    __tablename__ = "personal_funds"
    id = Column(Integer, primary_key=True, index=True)
    fund_address = Column(String(42), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    owner_address = Column(String(42), nullable=False)
    principal = Column(DECIMAL(18, 6), nullable=False)
    monthly_deposit = Column(DECIMAL(18, 6), nullable=False)
    current_age = Column(Integer, nullable=False)
    retirement_age = Column(Integer, nullable=False)
    desired_monthly = Column(DECIMAL(18, 6), nullable=False)
    years_payments = Column(Integer, nullable=False)
    interest_rate = Column(Integer, nullable=False)
    timelock_period = Column(Integer, nullable=False)
    timelock_end = Column(DateTime(timezone=True), nullable=False, index=True)
    initialized = Column(Boolean, default=False)
    retirement_started = Column(Boolean, default=False, index=True)
    retirement_start_time = Column(DateTime(timezone=True))
    early_retirement_approved = Column(Boolean, default=False)
    total_gross_deposited = Column(DECIMAL(18, 6), default=0)
    total_fees_paid = Column(DECIMAL(18, 6), default=0)
    total_net_to_fund = Column(DECIMAL(18, 6), default=0)
    total_balance = Column(DECIMAL(18, 6), default=0)
    available_balance = Column(DECIMAL(18, 6), default=0)
    total_invested = Column(DECIMAL(18, 6), default=0)
    total_withdrawn = Column(DECIMAL(18, 6), default=0)
    monthly_deposit_count = Column(Integer, default=0)
    extra_deposit_count = Column(Integer, default=0)
    withdrawal_count = Column(Integer, default=0)
    auto_withdrawal_enabled = Column(Boolean, default=False)
    auto_withdrawal_amount = Column(DECIMAL(18, 6), default=0)
    auto_withdrawal_interval = Column(Integer, default=2592000)
    next_auto_withdrawal_time = Column(DateTime(timezone=True), index=True)
    auto_withdrawal_execution_count = Column(Integer, default=0)
    last_auto_withdrawal_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_withdrawal_time = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="personal_fund")
    transactions = relationship("FundTransaction", back_populates="fund", cascade="all, delete-orphan")
    investments = relationship("FundInvestment", back_populates="fund", cascade="all, delete-orphan")

class FundTransaction(Base):
    __tablename__ = "fund_transactions"
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey('personal_funds.id', ondelete='CASCADE'), nullable=False, index=True)
    fund_address = Column(String(42), nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)
    gross_amount = Column(DECIMAL(18, 6))
    fee_amount = Column(DECIMAL(18, 6))
    net_amount = Column(DECIMAL(18, 6))
    protocol_address = Column(String(42))
    description = Column(Text)
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(Integer, nullable=False)
    block_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fund = relationship("PersonalFund", back_populates="transactions")

class FundInvestment(Base):
    __tablename__ = "fund_investments"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey('personal_funds.id', ondelete='CASCADE'), nullable=False, index=True)
    fund_address = Column(String(42), nullable=False)
    protocol_address = Column(String(42), nullable=False, index=True)
    protocol_name = Column(String(64))
    amount_invested = Column(DECIMAL(18, 6), nullable=False)
    current_value = Column(DECIMAL(18, 6), nullable=False)
    apy = Column(Integer)  
    investment_start = Column(DateTime(timezone=True), nullable=False, index=True)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    withdrawn_amount = Column(DECIMAL(18, 6), default=0)
    total_earnings = Column(DECIMAL(18, 6), default=0)
    transaction_hash = Column(String(66))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    fund = relationship("PersonalFund", back_populates="investments")

    __table_args__ = (
        Index('idx_fund_protocol', 'fund_id', 'protocol_address'),
        Index('idx_active_investments', 'fund_id', 'is_active'),
    )
