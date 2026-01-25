from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, DECIMAL,
    ForeignKey, Text, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PersonalFund(Base):
    __tablename__ = "personal_funds"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        unique=True,
        index=True
    )
    fund_address = Column(String(42), unique=True, nullable=False, index=True)
    owner_address = Column(String(42), nullable=False, index=True)
    total_deposited = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_withdrawn = Column(DECIMAL(18, 6), default=0, nullable=False)
    current_balance = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_fees_paid = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_invested = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_earnings = Column(DECIMAL(18, 6), default=0, nullable=False)
    timelock_end = Column(DateTime(timezone=True), nullable=False)
    retirement_started = Column(Boolean, default=False, nullable=False, index=True)
    retirement_date = Column(DateTime(timezone=True), nullable=True)
    early_retirement_approved = Column(Boolean, default=False, nullable=False)
    early_retirement_penalty = Column(DECIMAL(18, 6), default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_deposit_at = Column(DateTime(timezone=True), nullable=True)
    last_withdrawal_at = Column(DateTime(timezone=True), nullable=True)
    last_compound_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    creation_tx_hash = Column(String(66), nullable=False)
    creation_block_number = Column(Integer, nullable=False)
    owner = relationship("User", back_populates="personal_fund")
    
    transactions = relationship(
        "FundTransaction",
        back_populates="fund",
        cascade="all, delete-orphan",
        order_by="desc(FundTransaction.timestamp)"
    )
    
    investments = relationship(
        "FundInvestment",
        back_populates="fund",
        cascade="all, delete-orphan"
    )
    
    fee_record = relationship(
        "FundFeeRecord",
        back_populates="fund",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    early_retirement_requests = relationship(
        "EarlyRetirementRequest",
        back_populates="fund",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_personal_funds_owner', 'owner_id'),
        Index('idx_personal_funds_address', 'fund_address'),
        Index('idx_personal_funds_active', 'is_active'),
        Index('idx_personal_funds_retirement', 'retirement_started'),
        CheckConstraint('current_balance >= 0', name='check_balance_positive'),
        CheckConstraint('total_deposited >= 0', name='check_deposits_positive'),
    )
    
    def __repr__(self):
        return f"<PersonalFund(address={self.fund_address}, owner={self.owner_address}, balance={self.current_balance})>"
    
    @property
    def can_retire(self) -> bool:
        if self.retirement_started:
            return False
        if self.early_retirement_approved:
            return True
        return datetime.utcnow() >= self.timelock_end
    
    @property
    def days_until_retirement(self) -> int:
        if self.retirement_started or self.early_retirement_approved:
            return 0
        if datetime.utcnow() >= self.timelock_end:
            return 0
        delta = self.timelock_end - datetime.utcnow()
        return delta.days
    
    @property
    def net_balance(self) -> float:
        return float(self.current_balance - self.total_fees_paid)
    
    @property
    def total_return(self) -> float:
        return float(self.total_earnings - self.total_fees_paid)
    
    @property
    def roi_percentage(self) -> float:
        if self.total_deposited == 0:
            return 0.0
        return (self.total_return / float(self.total_deposited)) * 100
    
    @property
    def status(self) -> str:
        if not self.is_active:
            return "inactive"
        if self.retirement_started:
            return "retired"
        if self.early_retirement_approved:
            return "early_retirement_approved"
        if self.can_retire:
            return "ready_for_retirement"
        return "accumulating"

class FundTransaction(Base):
    __tablename__ = "fund_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(
        Integer, 
        ForeignKey('personal_funds.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    fund_address = Column(String(42), nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False, index=True)
    amount = Column(DECIMAL(18, 6), nullable=False)
    balance_after = Column(DECIMAL(18, 6), nullable=False)
    protocol_address = Column(String(42), nullable=True)
    protocol_name = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=False)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(DECIMAL(18, 6), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    fund = relationship("PersonalFund", back_populates="transactions")
    
    __table_args__ = (
        Index('idx_fund_transactions_fund', 'fund_id'),
        Index('idx_fund_transactions_type', 'transaction_type'),
        Index('idx_fund_transactions_hash', 'transaction_hash'),
        Index('idx_fund_transactions_date', 'timestamp'),
        UniqueConstraint('transaction_hash', 'fund_address', name='uq_tx_fund'),
    )
    def __repr__(self):
        return f"<FundTransaction(type={self.transaction_type}, amount={self.amount}, fund={self.fund_address[:10]}...)>"
    
    @property
    def is_deposit(self) -> bool:
        return self.transaction_type == 'deposit'
    
    @property
    def is_withdrawal(self) -> bool:
        return self.transaction_type == 'withdrawal'
    
    @property
    def is_fee(self) -> bool:
        return self.transaction_type == 'fee'
    
    @property
    def formatted_amount(self) -> str:
        return f"{float(self.amount):,.2f} USDC"