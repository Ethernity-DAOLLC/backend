from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class DeFiProtocol(Base):
    __tablename__ = "defi_protocols"
    id = Column(Integer, primary_key=True, index=True)
    protocol_address = Column(String(42), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    apy = Column(Integer, nullable=False)
    risk_level = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    verified = Column(Boolean, default=False, index=True)
    total_deposited = Column(DECIMAL(18, 6), default=0)
    added_timestamp = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    fund_investments = relationship("FundInvestment", back_populates="protocol", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint('risk_level BETWEEN 1 AND 3', name='check_risk_level'),
    )

class FundInvestment(Base):
    __tablename__ = "fund_investments"
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey('personal_funds.id', ondelete='CASCADE'), nullable=False)
    protocol_id = Column(Integer, ForeignKey('defi_protocols.id'), nullable=False)
    fund_address = Column(String(42), nullable=False)
    protocol_address = Column(String(42), nullable=False)
    amount_invested = Column(DECIMAL(18, 6), nullable=False)
    current_balance = Column(DECIMAL(18, 6), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    first_investment_at = Column(DateTime(timezone=True), nullable=False)
    last_update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    fund = relationship("PersonalFund", back_populates="investments")
    protocol = relationship("DeFiProtocol", back_populates="fund_investments")
