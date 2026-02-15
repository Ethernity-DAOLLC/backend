from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime,
    ForeignKey, Enum as SQLEnum, Boolean, Text, DECIMAL, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    FEE = "fee"

class InvestmentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class PersonalFund(Base):
    """
    Modelo de Fondo Personal de Retiro.
    Refleja el estado del Smart Contract PersonalFund.vy.

    Campos del contrato:
      owner, principal, monthlyDeposit, currentAge, retirementAge,
      desiredMonthly, yearsPayments, interestRate, createdAt,
      totalGrossDeposited, totalFeesPaid, totalNetToFund,
      totalBalance, totalInvested, availableBalance,
      monthlyDepositCount, extraDepositCount,
      retirementStarted, timelockEnd, earlyRetirementApproved,
      totalWithdrawn, withdrawalCount
    """
    __tablename__ = "personal_funds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )

    fund_address = Column(String(42), unique=True, nullable=False, index=True)
    owner_address = Column(String(42), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    total_balance = Column(DECIMAL(18, 6), default=0, nullable=False)        # totalBalance
    available_balance = Column(DECIMAL(18, 6), default=0, nullable=False)    # availableBalance
    invested_balance = Column(DECIMAL(18, 6), default=0, nullable=False)     # totalInvested
    total_deposited = Column(DECIMAL(18, 6), default=0, nullable=False)      # totalGrossDeposited
    total_withdrawn = Column(DECIMAL(18, 6), default=0, nullable=False)      # totalWithdrawn
    total_fees_paid = Column(DECIMAL(18, 6), default=0, nullable=False)      # totalFeesPaid
    total_earnings = Column(DECIMAL(18, 6), default=0, nullable=False)

    status = Column(String(20), default='active', nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_locked = Column(Boolean, default=False, nullable=False)

    retirement_started = Column(Boolean, default=False, nullable=False, index=True)
    retirement_date = Column(DateTime(timezone=True), nullable=True)
    early_retirement_approved = Column(Boolean, default=False, nullable=False)
    early_retirement_penalty = Column(DECIMAL(18, 6), default=0, nullable=False)
    timelock_end = Column(DateTime(timezone=True), nullable=True, index=True)

    retirement_age = Column(Integer, nullable=True)
    monthly_deposit_amount = Column(DECIMAL(18, 6), nullable=True)
    target_retirement_amount = Column(DECIMAL(18, 6), nullable=True)

    creation_tx_hash = Column(String(66), nullable=True)
    creation_block_number = Column(Integer, nullable=True)

    last_deposit_at = Column(DateTime(timezone=True), nullable=True)
    last_withdrawal_at = Column(DateTime(timezone=True), nullable=True)
    last_compound_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones
    owner = relationship("User", back_populates="personal_fund", foreign_keys=[user_id])
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
    early_retirement_requests = relationship(
        "EarlyRetirementRequest",
        back_populates="fund",
        cascade="all, delete-orphan"
    )
    fee_record = relationship(
        "FundFeeRecord",
        back_populates="fund",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_personal_funds_user', 'user_id'),
        Index('idx_personal_funds_address', 'fund_address'),
        Index('idx_personal_fund_status', 'status', 'is_active'),
        Index('idx_personal_funds_retirement', 'retirement_started'),
    )

    def __repr__(self):
        return f"<PersonalFund(id={self.id}, owner={self.user_id}, balance={self.total_balance})>"

    @property
    def is_ready_for_retirement(self) -> bool:
        if not self.timelock_end:
            return False
        return datetime.utcnow() >= self.timelock_end

    @property
    def days_until_retirement(self) -> int:
        if not self.timelock_end:
            return -1
        if self.retirement_started:
            return 0
        delta = self.timelock_end - datetime.utcnow()
        return max(0, delta.days)

    @property
    def fund_status_text(self) -> str:
        if self.retirement_started:
            return "RETIRED"
        elif self.early_retirement_approved:
            return "EARLY_RETIREMENT_APPROVED"
        elif self.is_ready_for_retirement:
            return "READY_FOR_RETIREMENT"
        elif not self.is_active:
            return "INACTIVE"
        else:
            return "ACCUMULATING"


class FundTransaction(Base):
    __tablename__ = "fund_transactions"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("personal_funds.id", ondelete='CASCADE'), nullable=False, index=True)
    fund_address = Column(String(42), nullable=False, index=True)

    transaction_type = Column(String(50), nullable=False, index=True)
    amount = Column(DECIMAL(18, 6), nullable=False)
    balance_after = Column(DECIMAL(18, 6), nullable=False)

    protocol_address = Column(String(42), nullable=True)
    protocol_name = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    from_address = Column(String(42), nullable=True)
    to_address = Column(String(42), nullable=True)

    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=False)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(DECIMAL(18, 6), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=True)  # populated = timestamp

    fund = relationship("PersonalFund", back_populates="transactions", foreign_keys=[fund_id])

    __table_args__ = (
        Index('idx_fund_transactions_fund', 'fund_id'),
        Index('idx_fund_transactions_type', 'transaction_type'),
        Index('idx_fund_transactions_date', 'timestamp'),
        Index('idx_fund_transactions_hash', 'transaction_hash'),
    )

    def __repr__(self):
        return f"<FundTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class FundInvestment(Base):
    __tablename__ = "fund_investments"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("personal_funds.id", ondelete='CASCADE'), nullable=False, index=True)
    protocol_id = Column(Integer, ForeignKey("defi_protocols.id", ondelete='SET NULL'), nullable=True, index=True)

    fund_address = Column(String(42), nullable=False)
    protocol_address = Column(String(42), nullable=False)

    amount_invested = Column(DECIMAL(18, 6), nullable=False)       # amount en el contrato
    current_balance = Column(DECIMAL(18, 6), nullable=False)       # valor actual
    expected_return = Column(DECIMAL(18, 6), nullable=True)
    actual_return = Column(DECIMAL(18, 6), default=0, nullable=False)
    apy_at_investment = Column(DECIMAL(10, 2), nullable=True)

    is_active = Column(Boolean, nullable=True, index=True)
    first_investment_at = Column(DateTime(timezone=True), nullable=False)   # invested_at en contrato
    last_update_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    transaction_hash = Column(String(66), nullable=True)

    fund = relationship("PersonalFund", back_populates="investments", foreign_keys=[fund_id])
    protocol = relationship("DeFiProtocol", back_populates="fund_investments", foreign_keys=[protocol_id])

    __table_args__ = (
        Index('idx_fund_investment_fund', 'fund_id'),
        Index('idx_fund_investment_protocol', 'protocol_id'),
        Index('idx_fund_investment_active', 'is_active'),
    )

    def __repr__(self):
        return f"<FundInvestment(fund={self.fund_id}, protocol={self.protocol_id}, amount={self.amount_invested})>"

    @property
    def roi(self) -> float:
        if not self.amount_invested or self.amount_invested == 0:
            return 0.0
        return (float(self.actual_return) / float(self.amount_invested)) * 100