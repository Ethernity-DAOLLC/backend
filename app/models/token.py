from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class TokenHolder(Base):
    __tablename__ = "token_holders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    wallet_address = Column(String(42), nullable=False, unique=True, index=True)
    balance = Column(DECIMAL(78, 18), default=1.0, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    has_activity_this_month = Column(Boolean, default=True, index=True)
    last_activity_timestamp = Column(DateTime(timezone=True))
    last_activity_type = Column(String(64))
    burned_this_month = Column(Boolean, default=False)
    renewed_this_month = Column(Boolean, default=False)
    total_burns = Column(Integer, default=0)
    total_renews = Column(Integer, default=0)
    holder_since = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="token_holder")
    activities = relationship("TokenActivity", back_populates="holder", cascade="all, delete-orphan")

class TokenActivity(Base):
    __tablename__ = "token_activities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False)
    activity_type = Column(String(64), nullable=False, index=True)
    description = Column(Text)
    transaction_hash = Column(String(66))
    block_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    holder = relationship("TokenHolder", back_populates="activities")

class TokenMonthlyStats(Base):
    __tablename__ = "token_monthly_stats"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    total_burned = Column(DECIMAL(78, 18), default=0, nullable=False)
    total_renewed = Column(DECIMAL(78, 18), default=0, nullable=False)
    holders_burned = Column(Integer, default=0, nullable=False)
    holders_renewed = Column(Integer, default=0, nullable=False)
    burn_executed_at = Column(DateTime(timezone=True))
    renew_executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_year_month', 'year', 'month', unique=True),
    )