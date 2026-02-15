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
    """Estados posibles de un fondo personal"""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"

class TransactionType(str, enum.Enum):
    """Tipos de transacciones en el fondo"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INVESTMENT = "investment"
    RETURN = "return"
    FEE = "fee"

class InvestmentStatus(str, enum.Enum):
    """Estados de una inversión"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

# ---------------------------------------------------------------------------
# 📊 MODELO: PersonalFund
# ---------------------------------------------------------------------------

class PersonalFund(Base):
    """
    Modelo de Fondo Personal de Retiro
    
    Representa un fondo de retiro individual para un usuario.
    Almacena balance, configuración de inversiones y estado del fondo.
    """
    __tablename__ = "personal_funds"

    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete='CASCADE'), 
        nullable=False,
        unique=True,  # Un usuario solo puede tener un fondo
        index=True
    )
    
    # Información del fondo
    fund_address = Column(String(42), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Balances
    total_balance = Column(DECIMAL(18, 6), default=0, nullable=False)
    available_balance = Column(DECIMAL(18, 6), default=0, nullable=False)
    invested_balance = Column(DECIMAL(18, 6), default=0, nullable=False)
    
    # Estado del fondo
    status = Column(
        SQLEnum(FundStatus), 
        default=FundStatus.ACTIVE, 
        nullable=False,
        index=True
    )
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # ✅ FIX: Campos que user.py necesita
    retirement_started = Column(Boolean, default=False, nullable=False, index=True)
    early_retirement_approved = Column(Boolean, default=False, nullable=False)
    timelock_end = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Configuración de retiro
    retirement_age = Column(Integer, nullable=True)
    monthly_deposit_amount = Column(DECIMAL(18, 6), nullable=True)
    target_retirement_amount = Column(DECIMAL(18, 6), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False
    )
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    
    # Relación con User
    owner = relationship(
        "User", 
        back_populates="personal_fund",
        foreign_keys=[user_id]
    )
    
    # Transacciones del fondo
    transactions = relationship(
        "FundTransaction", 
        back_populates="fund", 
        cascade="all, delete-orphan",
        order_by="desc(FundTransaction.created_at)"
    )
    
    # Inversiones del fondo
    investments = relationship(
        "FundInvestment", 
        back_populates="fund", 
        cascade="all, delete-orphan"
    )
    
    # ✅ FIX: Relaciones con treasury models
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
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_personal_fund_user', 'user_id'),
        Index('idx_personal_fund_address', 'fund_address'),
        Index('idx_personal_fund_status', 'status', 'is_active'),
        Index('idx_personal_fund_retirement', 'retirement_started'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos y propiedades
    # -------------------------------------------------------------------------
    
    def __repr__(self):
        return f"<PersonalFund(id={self.id}, owner={self.user_id}, balance={self.total_balance})>"
    
    @property
    def invested_percentage(self) -> float:
        """Porcentaje del balance que está invertido"""
        if self.total_balance == 0:
            return 0.0
        return (float(self.invested_balance) / float(self.total_balance)) * 100
    
    @property
    def is_ready_for_retirement(self) -> bool:
        """Verifica si el fondo está listo para retiro"""
        if not self.timelock_end:
            return False
        return datetime.utcnow() >= self.timelock_end
    
    @property
    def days_until_retirement(self) -> int:
        """Días restantes hasta que se pueda retirar"""
        if not self.timelock_end:
            return -1
        if self.retirement_started:
            return 0
        
        delta = self.timelock_end - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def fund_status_text(self) -> str:
        """Estado del fondo en texto legible"""
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

# ---------------------------------------------------------------------------
# 📊 MODELO: FundTransaction
# ---------------------------------------------------------------------------

class FundTransaction(Base):
    """
    Modelo de Transacción de Fondo
    
    Registra todas las transacciones (depósitos, retiros, inversiones)
    realizadas en un fondo personal.
    """
    __tablename__ = "fund_transactions"

    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(
        Integer, 
        ForeignKey("personal_funds.id", ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    transaction_type = Column(
        SQLEnum(TransactionType), 
        nullable=False,
        index=True
    )
    amount = Column(DECIMAL(18, 6), nullable=False)
    
    description = Column(Text, nullable=True)
    
    # Información blockchain
    transaction_hash = Column(String(66), nullable=True, unique=True, index=True)
    block_number = Column(Integer, nullable=True)
    from_address = Column(String(42), nullable=True)
    to_address = Column(String(42), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    fund = relationship(
        "PersonalFund", 
        back_populates="transactions",
        foreign_keys=[fund_id]
    )
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_fund_transaction_fund', 'fund_id'),
        Index('idx_fund_transaction_type', 'transaction_type'),
        Index('idx_fund_transaction_date', 'created_at'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos
    # -------------------------------------------------------------------------
    
    def __repr__(self):
        return (
            f"<FundTransaction(id={self.id}, "
            f"type={self.transaction_type}, "
            f"amount={self.amount})>"
        )
    
    @property
    def is_deposit(self) -> bool:
        return self.transaction_type == TransactionType.DEPOSIT
    
    @property
    def is_withdrawal(self) -> bool:
        return self.transaction_type == TransactionType.WITHDRAWAL
    
    @property
    def has_blockchain_confirmation(self) -> bool:
        return self.transaction_hash is not None

# ---------------------------------------------------------------------------
# 📊 MODELO: FundInvestment
# ---------------------------------------------------------------------------

class FundInvestment(Base):
    """
    Modelo de Inversión de Fondo
    
    Registra inversiones realizadas desde un fondo personal
    hacia protocolos DeFi.
    """
    __tablename__ = "fund_investments"

    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(
        Integer, 
        ForeignKey("personal_funds.id", ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # ✅ FIX: Usar protocol_id en lugar de project_id
    protocol_id = Column(
        Integer, 
        ForeignKey("defi_protocols.id", ondelete='SET NULL'), 
        nullable=True,
        index=True
    )
    
    # ⚠️ COMENTADO: Project no existe aún
    # project_id = Column(
    #     Integer, 
    #     ForeignKey("projects.id", ondelete='SET NULL'), 
    #     nullable=True
    # )
    
    # Montos
    amount = Column(DECIMAL(18, 6), nullable=False)
    expected_return = Column(DECIMAL(18, 6), nullable=True)
    actual_return = Column(DECIMAL(18, 6), default=0, nullable=False)
    current_value = Column(DECIMAL(18, 6), nullable=True)
    
    # APY al momento de inversión
    apy_at_investment = Column(DECIMAL(10, 2), nullable=True)
    
    # Estado
    status = Column(
        SQLEnum(InvestmentStatus), 
        default=InvestmentStatus.PENDING, 
        nullable=False,
        index=True
    )
    
    # Timestamps
    invested_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Información blockchain
    transaction_hash = Column(String(66), nullable=True, index=True)

    fund = relationship(
        "PersonalFund", 
        back_populates="investments",
        foreign_keys=[fund_id]
    )
    
    protocol = relationship(
        "DeFiProtocol", 
        back_populates="fund_investments",
        foreign_keys=[protocol_id]
    )
    
    # ⚠️ COMENTADO: Hasta que exista Project model
    # project = relationship(
    #     "Project", 
    #     back_populates="fund_investments",
    #     foreign_keys=[project_id]
    # )

    __table_args__ = (
        Index('idx_fund_investment_fund', 'fund_id'),
        Index('idx_fund_investment_protocol', 'protocol_id'),
        Index('idx_fund_investment_status', 'status'),
        Index('idx_fund_investment_date', 'invested_at'),
    )

    def __repr__(self):
        return (
            f"<FundInvestment(id={self.id}, "
            f"fund={self.fund_id}, "
            f"protocol={self.protocol_id}, "
            f"amount={self.amount}, "
            f"status={self.status})>"
        )
    
    @property
    def roi(self) -> float:
        """Return on Investment en porcentaje"""
        if self.amount == 0:
            return 0.0
        return (float(self.actual_return) / float(self.amount)) * 100
    
    @property
    def is_active(self) -> bool:
        return self.status == InvestmentStatus.ACTIVE
    
    @property
    def is_completed(self) -> bool:
        return self.status == InvestmentStatus.COMPLETED
    
    @property
    def profit_loss(self) -> float:
        """Ganancia o pérdida actual"""
        if not self.current_value:
            return 0.0
        return float(self.current_value - self.amount)

"""
CAMBIOS REALIZADOS:


MIGRACIÓN NECESARIA:

Si ya tienes datos en producción:

```sql
-- Agregar campos nuevos a personal_funds
ALTER TABLE personal_funds 
ADD COLUMN retirement_started BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN early_retirement_approved BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN timelock_end TIMESTAMP WITH TIME ZONE,
ADD COLUMN fund_address VARCHAR(42) UNIQUE,
ADD COLUMN retirement_age INTEGER,
ADD COLUMN monthly_deposit_amount NUMERIC(18,6),
ADD COLUMN target_retirement_amount NUMERIC(18,6);

-- Agregar índices
CREATE INDEX idx_personal_fund_retirement ON personal_funds(retirement_started);
CREATE INDEX idx_personal_fund_timelock ON personal_funds(timelock_end);

-- Actualizar fund_investments si existe project_id
-- ALTER TABLE fund_investments DROP COLUMN project_id;
ALTER TABLE fund_investments 
ADD COLUMN protocol_id INTEGER REFERENCES defi_protocols(id) ON DELETE SET NULL;
```

TESTING:

```python
from app.models.personal_fund import PersonalFund
from app.models.user import User
from app.db.session import SessionLocal

db = SessionLocal()

# Crear usuario y fondo
user = User(wallet_address="0x123...")
db.add(user)
db.commit()

fund = PersonalFund(
    user_id=user.id,
    fund_address="0xABC...",
    name="My Retirement Fund",
    total_balance=1000.00
)
db.add(fund)
db.commit()

# Verificar propiedades de User funcionan
print(user.has_fund)  # ✅ True
print(user.is_in_retirement)  # ✅ False (fund.retirement_started = False)
print(user.get_fund_status())  # ✅ "ACCUMULATING"

# Verificar propiedades de Fund
print(fund.fund_status_text)  # ✅ "ACCUMULATING"
print(fund.days_until_retirement)  # ✅ número o -1

print("✅ All tests passed!")
```
"""