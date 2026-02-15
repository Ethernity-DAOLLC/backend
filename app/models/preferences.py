from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, DECIMAL,
    ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import logging

logger = logging.getLogger(__name__)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        unique=True,
        index=True
    )
    wallet_address = Column(String(42), nullable=False, index=True)
    selected_protocol_id = Column(
        Integer, 
        ForeignKey('defi_protocols.id'),
        nullable=True
    )

    auto_compound = Column(Boolean, default=True, nullable=False)
    risk_tolerance = Column(Integer, default=2, nullable=False)  
    strategy_type = Column(Integer, default=0, nullable=False, index=True)
    diversification_percent = Column(Integer, default=0, nullable=False)
    rebalance_threshold = Column(Integer, default=0, nullable=False)
    total_deposited = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_withdrawn = Column(DECIMAL(18, 6), default=0, nullable=False)

    last_update = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    user = relationship("User", back_populates="preferences")
    selected_protocol = relationship("DeFiProtocol", foreign_keys=[selected_protocol_id])
    protocol_deposits = relationship(
        "UserProtocolDeposit", 
        back_populates="preference", 
        cascade="all, delete-orphan",
        foreign_keys="UserProtocolDeposit.preference_id" 
    )

    __table_args__ = (
        CheckConstraint(
            'risk_tolerance BETWEEN 1 AND 3', 
            name='check_risk_tolerance'
        ),
        CheckConstraint(
            'strategy_type BETWEEN 0 AND 3', 
            name='check_strategy_type'
        ),
        CheckConstraint(
            'diversification_percent BETWEEN 0 AND 100',
            name='check_diversification_percent'
        ),
        Index('idx_user_preferences_strategy', 'strategy_type'),
    )
    
    def __repr__(self):
        strategy_names = {
            0: "Manual",
            1: "Best APY",
            2: "Risk-Adjusted",
            3: "Diversified"
        }
        return (
            f"<UserPreference(user_id={self.user_id}, "
            f"strategy={strategy_names.get(self.strategy_type, 'Unknown')}, "
            f"risk_tolerance={self.risk_tolerance})>"
        )
    
    @property
    def strategy_name(self) -> str:
        strategy_names = {
            0: "Manual Selection",
            1: "Best APY",
            2: "Risk-Adjusted Returns",
            3: "Diversified Portfolio"
        }
        return strategy_names.get(self.strategy_type, "Unknown")
    
    @property
    def risk_level_name(self) -> str:
        risk_names = {1: "Low", 2: "Medium", 3: "High"}
        return risk_names.get(self.risk_tolerance, "Unknown")

class UserProtocolDeposit(Base):
    __tablename__ = "user_protocol_deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, 
        ForeignKey('users.id'), 
        nullable=False, 
        index=True
    )
    protocol_id = Column(
        Integer, 
        ForeignKey('defi_protocols.id'), 
        nullable=False, 
        index=True
    )
    preference_id = Column(
        Integer,
        ForeignKey('user_preferences.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    total_deposited = Column(DECIMAL(18, 6), default=0, nullable=False)
    last_deposit_at = Column(DateTime(timezone=True), nullable=True)
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

    preference = relationship(
        "UserPreference",
        back_populates="protocol_deposits",
        foreign_keys=[preference_id]  
    )
    user = relationship("User")
    protocol = relationship("DeFiProtocol")

    __table_args__ = (
        UniqueConstraint('user_id', 'protocol_id', name='uq_user_protocol'),
        Index('idx_user_protocol_deposits_user', 'user_id'),
        Index('idx_user_protocol_deposits_protocol', 'protocol_id'),
        Index('idx_user_protocol_deposits_preference', 'preference_id'),
    )
    
    def __repr__(self):
        return (
            f"<UserProtocolDeposit(user_id={self.user_id}, "
            f"protocol_id={self.protocol_id}, "
            f"total={self.total_deposited})>"
        )