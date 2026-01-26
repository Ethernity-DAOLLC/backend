from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text
from sqlalchemy.orm import relationship
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
    name = Column(String(255), nullable=False, unique=True)
    protocol_type = Column(SQLEnum(ProtocolType), nullable=False)
    contract_address = Column(String(66), nullable=True)
    description = Column(Text, nullable=True)
    apy = Column(Numeric(10, 2), nullable=True)
    tvl = Column(Numeric(20, 2), nullable=True)
    risk_level = Column(Integer, default=5, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    fund_investments = relationship("FundInvestment", back_populates="protocol", cascade="all, delete-orphan")
    apy_history = relationship("ProtocolAPYHistory", back_populates="protocol", cascade="all, delete-orphan")

class ProtocolAPYHistory(Base):
    __tablename__ = "protocol_apy_history"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("defi_protocols.id"), nullable=False)
    apy = Column(Numeric(10, 2), nullable=False)
    tvl = Column(Numeric(20, 2), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    protocol = relationship("DeFiProtocol", back_populates="apy_history")