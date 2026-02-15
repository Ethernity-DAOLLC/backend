from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime,
    ForeignKey, Enum as SQLEnum, Boolean, Text, DECIMAL, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.base_class import Base

class ProtocolType(str, enum.Enum):
    DEX = "dex"
    LENDING = "lending"
    STAKING = "staking"
    YIELD = "yield"
    OTHER = "other"

class DeFiProtocol(Base):
    __tablename__ = "defi_protocols"
    id = Column(Integer, primary_key=True, index=True)
    protocol_address = Column(String(42), nullable=False, unique=True, index=True)

    name = Column(String(64), nullable=False)
    apy = Column(Integer, nullable=False)                          # basis points: 100 = 1%
    risk_level = Column(Integer, nullable=False)                   # 1=low, 2=medium, 3=high
    is_active = Column(Boolean, default=True, nullable=True, index=True)
    verified = Column(Boolean, default=False, nullable=True, index=True)
    total_deposited = Column(DECIMAL(18, 6), default=0, nullable=True)
    tvl = Column(Numeric(20, 2), nullable=True)                    # extra para UI

    description = Column(Text, nullable=True)
    protocol_type = Column(String(20), nullable=True)

    added_timestamp = Column(DateTime(timezone=True), nullable=False)   # addedTimestamp
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)  # lastUpdated
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    fund_investments = relationship(
        "FundInvestment",
        back_populates="protocol",
        cascade="all, delete-orphan"
    )
    apy_history = relationship(
        "ProtocolAPYHistory",
        back_populates="protocol",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_defi_protocols_active', 'is_active'),
        Index('idx_defi_protocols_risk', 'risk_level'),
        Index('idx_defi_protocols_verified', 'verified'),
    )

    def __repr__(self):
        return f"<DeFiProtocol(name={self.name}, apy={self.apy}, risk={self.risk_level})>"

    @property
    def apy_percentage(self) -> float:
        return self.apy / 100.0

    @property
    def risk_name(self) -> str:
        names = {1: "Low", 2: "Medium", 3: "High"}
        return names.get(self.risk_level, "Unknown")

class ProtocolAPYHistory(Base):
    __tablename__ = "protocol_apy_history"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("defi_protocols.id"), nullable=False, index=True)
    apy = Column(Numeric(10, 2), nullable=False)
    tvl = Column(Numeric(20, 2), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    protocol = relationship("DeFiProtocol", back_populates="apy_history")

    def __repr__(self):
        return f"<ProtocolAPYHistory(protocol={self.protocol_id}, apy={self.apy})>"