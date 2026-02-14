from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base

class FundStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INVESTMENT = "investment"
    RETURN = "return"

class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class PersonalFund(Base):
    __tablename__ = "personal_funds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_balance = Column(Numeric(20, 8), default=0, nullable=False)
    available_balance = Column(Numeric(20, 8), default=0, nullable=False)
    invested_balance = Column(Numeric(20, 8), default=0, nullable=False)
    status = Column(SQLEnum(FundStatus), default=FundStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    owner = relationship("User", back_populates="personal_fund")
    transactions = relationship("FundTransaction", back_populates="fund", cascade="all, delete-orphan")
    investments = relationship("FundInvestment", back_populates="fund", cascade="all, delete-orphan")

class FundTransaction(Base):
    __tablename__ = "fund_transactions"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("personal_funds.id"), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    description = Column(Text, nullable=True)
    transaction_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    fund = relationship("PersonalFund", back_populates="transactions")

class FundInvestment(Base):
    __tablename__ = "fund_investments"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("personal_funds.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    expected_return = Column(Numeric(20, 8), nullable=True)
    actual_return = Column(Numeric(20, 8), default=0, nullable=False)
    status = Column(SQLEnum(InvestmentStatus), default=InvestmentStatus.PENDING, nullable=False)
    invested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    fund = relationship("PersonalFund", back_populates="investments")
    project = relationship("Project", back_populates="fund_investments")