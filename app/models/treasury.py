from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, DECIMAL, 
    ForeignKey, Text, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import logging

logger = logging.getLogger(__name__)

class TreasuryStats(Base):
    __tablename__ = "treasury_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    total_balance = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_fees_collected_usdc = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_fees_collected_all_time = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_fees_withdrawn = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_funds_registered = Column(Integer, default=0, nullable=False)
    active_funds_count = Column(Integer, default=0, nullable=False)
    total_early_retirement_requests = Column(Integer, default=0, nullable=False)
    pending_requests_count = Column(Integer, default=0, nullable=False)
    approved_early_retirements = Column(Integer, default=0, nullable=False)
    rejected_early_retirements = Column(Integer, default=0, nullable=False)
    
    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    __table_args__ = (
        CheckConstraint('total_balance >= 0', name='check_treasury_balance_positive'),
        CheckConstraint('total_fees_collected_usdc >= 0', name='check_fees_positive'),
        Index('idx_treasury_stats_updated', 'last_updated'),
    )
    
    def __repr__(self):
        return f"<TreasuryStats(balance={self.total_balance}, fees={self.total_fees_collected_usdc})>"
    
    @property
    def net_balance(self) -> float:
        """Balance neto después de retiros"""
        return float(self.total_fees_collected_usdc - self.total_fees_withdrawn)

class FundFeeRecord(Base):
    __tablename__ = "fund_fee_records"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(
        Integer, 
        ForeignKey('personal_funds.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    fund_address = Column(String(42), nullable=False, index=True)
    owner_address = Column(String(42), nullable=True, index=True)
    total_fees_paid = Column(DECIMAL(18, 6), default=0, nullable=False)
    fee_count = Column(Integer, default=0, nullable=False)
    last_fee_timestamp = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    fund = relationship("PersonalFund", back_populates="fee_record")
    
    __table_args__ = (
        Index('idx_fund_fee_records_fund', 'fund_id'),
        Index('idx_fund_fee_records_address', 'fund_address'),
        CheckConstraint('total_fees_paid >= 0', name='check_fees_paid_positive'),
    )
    
    def __repr__(self):
        return f"<FundFeeRecord(fund_address={self.fund_address}, total={self.total_fees_paid})>"

class EarlyRetirementRequest(Base):
    __tablename__ = "early_retirement_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(
        Integer, 
        ForeignKey('personal_funds.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    requester_id = Column(
        Integer, 
        ForeignKey('users.id'), 
        nullable=False, 
        index=True
    )
    fund_address = Column(String(42), nullable=False, index=True)
    requester_address = Column(String(42), nullable=False, index=True)
    proposal_id = Column(Integer, nullable=True, index=True)
    reason = Column(Text, nullable=False)
    current_balance = Column(DECIMAL(18, 6), nullable=True)
    penalty_amount = Column(DECIMAL(18, 6), nullable=True)
    net_amount = Column(DECIMAL(18, 6), nullable=True)
    approved = Column(Boolean, default=False, nullable=False)
    rejected = Column(Boolean, default=False, nullable=False)
    processed = Column(Boolean, default=False, nullable=False, index=True)
    votes_for = Column(DECIMAL(78, 18), default=0, nullable=False)
    votes_against = Column(DECIMAL(78, 18), default=0, nullable=False)
    
    request_timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    processed_timestamp = Column(DateTime(timezone=True), nullable=True)
    reviewer_address = Column(String(42), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    transaction_hash = Column(String(66), nullable=True, index=True)
    fund = relationship("PersonalFund", back_populates="early_retirement_requests")
    requester = relationship("User")
    
    __table_args__ = (
        Index('idx_early_retirement_fund', 'fund_id'),
        Index('idx_early_retirement_processed', 'processed'),
        Index('idx_early_retirement_date', 'request_timestamp'),
    )
    
    def __repr__(self):
        return f"<EarlyRetirementRequest(fund={self.fund_address}, status={'approved' if self.approved else 'rejected' if self.rejected else 'pending'})>"
    
    @property
    def is_pending(self) -> bool:
        return not self.processed
    
    @property
    def is_approved(self) -> bool:
        return self.processed and self.approved
    
    @property
    def is_rejected(self) -> bool:
        return self.processed and self.rejected
    
    @property
    def status(self) -> str:
        if not self.processed:
            return "pending"
        return "approved" if self.approved else "rejected"
    
    @property
    def penalty_percentage(self) -> float:
        if not self.current_balance or self.current_balance == 0:
            return 0.0
        return (float(self.penalty_amount or 0) / float(self.current_balance)) * 100

class TreasuryWithdrawal(Base):
    __tablename__ = "treasury_withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(
        Integer, 
        ForeignKey('proposals.id'), 
        nullable=False, 
        index=True
    )
    
    recipient_address = Column(String(42), nullable=False, index=True)
    amount = Column(DECIMAL(18, 6), nullable=False)
    purpose = Column(Text, nullable=False)
    approved_by_governance = Column(Boolean, default=False, nullable=False)
    executed = Column(Boolean, default=False, nullable=False, index=True)
    transaction_hash = Column(String(66), nullable=True, index=True)
    block_number = Column(Integer, nullable=True)
    
    requested_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    proposal = relationship("Proposal")
    
    __table_args__ = (
        Index('idx_treasury_withdrawal_proposal', 'proposal_id'),
        Index('idx_treasury_withdrawal_executed', 'executed'),
        CheckConstraint('amount > 0', name='check_withdrawal_amount_positive'),
    )
    
    def __repr__(self):
        return f"<TreasuryWithdrawal(amount={self.amount}, recipient={self.recipient_address[:10]}...)>"
    
    @property
    def status(self) -> str:
        """Estado actual del retiro"""
        if self.executed:
            return "executed"
        elif self.approved_by_governance:
            return "approved"
        else:
            return "pending"