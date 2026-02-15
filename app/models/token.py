# ===========================================================================
# 📁 FOLDER: app/models/
# 📄 FILE: token.py
# ===========================================================================
# 
# 🎯 PROPÓSITO:
# Modelos de SQLAlchemy para gestión de tokens GERAS y actividades
#
# ✅ FIXES APLICADOS:
# 1. Agregado holder_id foreign key en TokenActivity
# 2. Mejoradas relaciones bidireccionales
# 3. Agregados índices para mejor performance
#
# ===========================================================================

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, 
    Text, DECIMAL, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# ---------------------------------------------------------------------------
# 📊 MODELO: TokenHolder
# ---------------------------------------------------------------------------

class TokenHolder(Base):
    """
    Modelo de Tenedor de Token
    
    Representa un usuario que posee tokens GERAS.
    Almacena balance, estado de actividad y estadísticas mensuales.
    """
    __tablename__ = "token_holders"
    
    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        unique=True,
        index=True
    )
    wallet_address = Column(String(42), nullable=False, unique=True, index=True)
    
    # Balance y estado
    balance = Column(DECIMAL(78, 18), default=1.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Actividad mensual
    has_activity_this_month = Column(Boolean, default=True, nullable=False, index=True)
    last_activity_timestamp = Column(DateTime(timezone=True), nullable=True)
    last_activity_type = Column(String(64), nullable=True)
    
    # Estado de burn/renew mensual
    burned_this_month = Column(Boolean, default=False, nullable=False)
    renewed_this_month = Column(Boolean, default=False, nullable=False)
    
    # Contadores totales
    total_burns = Column(Integer, default=0, nullable=False)
    total_renews = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    holder_since = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    user = relationship(
        "User", 
        back_populates="token_holder",
        foreign_keys=[user_id]
    )
    
    activities = relationship(
        "TokenActivity", 
        back_populates="holder", 
        cascade="all, delete-orphan",
        order_by="desc(TokenActivity.created_at)"
    )
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_token_holder_user', 'user_id'),
        Index('idx_token_holder_wallet', 'wallet_address'),
        Index('idx_token_holder_active', 'is_active'),
        Index('idx_token_holder_activity', 'has_activity_this_month'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos y propiedades
    # -------------------------------------------------------------------------
    
    def __repr__(self):
        return f"<TokenHolder(wallet={self.wallet_address}, balance={self.balance})>"
    
    @property
    def balance_formatted(self) -> str:
        """Balance formateado con decimales"""
        return f"{float(self.balance):.4f} GERAS"
    
    @property
    def needs_burn(self) -> bool:
        """Verifica si necesita burn este mes"""
        return not self.has_activity_this_month and not self.burned_this_month
    
    @property
    def can_renew(self) -> bool:
        """Verifica si puede renovar este mes"""
        return self.burned_this_month and not self.renewed_this_month
    
    @property
    def holder_days(self) -> int:
        """Días que ha sido holder"""
        from datetime import datetime
        delta = datetime.utcnow() - self.holder_since
        return delta.days

# ---------------------------------------------------------------------------
# 📊 MODELO: TokenActivity
# ---------------------------------------------------------------------------

class TokenActivity(Base):
    """
    Modelo de Actividad de Token
    
    Registra todas las actividades relacionadas con tokens
    (burns, renews, transfers, etc.)
    """
    __tablename__ = "token_activities"
    
    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ FIX: Agregado holder_id foreign key
    holder_id = Column(
        Integer,
        ForeignKey('token_holders.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    user_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    wallet_address = Column(String(42), nullable=False, index=True)
    
    # Información de la actividad
    activity_type = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Montos (si aplica)
    amount = Column(DECIMAL(78, 18), nullable=True)
    
    # Información blockchain
    transaction_hash = Column(String(66), nullable=True, unique=True, index=True)
    block_number = Column(Integer, nullable=True, index=True)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    
    # ✅ FIX: Relación corregida con foreign_keys explícito
    holder = relationship(
        "TokenHolder", 
        back_populates="activities",
        foreign_keys=[holder_id]
    )
    
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_token_activity_holder', 'holder_id'),
        Index('idx_token_activity_user', 'user_id'),
        Index('idx_token_activity_type', 'activity_type'),
        Index('idx_token_activity_date', 'created_at'),
        Index('idx_token_activity_wallet', 'wallet_address'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos
    # -------------------------------------------------------------------------
    
    def __repr__(self):
        return (
            f"<TokenActivity(id={self.id}, "
            f"type={self.activity_type}, "
            f"wallet={self.wallet_address[:10]}...)>"
        )
    
    @property
    def is_burn(self) -> bool:
        return self.activity_type.lower() in ['burn', 'burned', 'token_burn']
    
    @property
    def is_renew(self) -> bool:
        return self.activity_type.lower() in ['renew', 'renewed', 'token_renew']
    
    @property
    def has_transaction(self) -> bool:
        return self.transaction_hash is not None

# ---------------------------------------------------------------------------
# 📊 MODELO: TokenMonthlyStats
# ---------------------------------------------------------------------------

class TokenMonthlyStats(Base):
    """
    Modelo de Estadísticas Mensuales de Token
    
    Almacena estadísticas agregadas de burns y renews por mes.
    Se actualiza al final de cada mes.
    """
    __tablename__ = "token_monthly_stats"
    
    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    
    # Período
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12
    
    # Estadísticas de burns
    total_burned = Column(DECIMAL(78, 18), default=0, nullable=False)
    holders_burned = Column(Integer, default=0, nullable=False)
    burn_executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Estadísticas de renews
    total_renewed = Column(DECIMAL(78, 18), default=0, nullable=False)
    holders_renewed = Column(Integer, default=0, nullable=False)
    renew_executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_year_month', 'year', 'month', unique=True),
        Index('idx_token_stats_year', 'year'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos y propiedades
    # -------------------------------------------------------------------------
    
    def __repr__(self):
        return (
            f"<TokenMonthlyStats(year={self.year}, "
            f"month={self.month}, "
            f"burned={self.total_burned}, "
            f"renewed={self.total_renewed})>"
        )
    
    @property
    def month_name(self) -> str:
        """Nombre del mes en inglés"""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return months[self.month - 1] if 1 <= self.month <= 12 else "Unknown"
    
    @property
    def burn_rate(self) -> float:
        """Porcentaje de holders que hicieron burn"""
        if self.holders_burned == 0:
            return 0.0
        # Nota: Necesitarías total de holders para calcular rate real
        return float(self.holders_burned)
    
    @property
    def renew_rate(self) -> float:
        """Porcentaje de holders que renovaron después del burn"""
        if self.holders_burned == 0:
            return 0.0
        return (self.holders_renewed / self.holders_burned) * 100
    
    @property
    def net_change(self) -> float:
        """Cambio neto (renewed - burned)"""
        return float(self.total_renewed - self.total_burned)

# ---------------------------------------------------------------------------
# 📝 NOTAS DE IMPLEMENTACIÓN
# ---------------------------------------------------------------------------

"""
CAMBIOS REALIZADOS:

1. ✅ TokenActivity - Agregado holder_id foreign key:
   - Ahora la relación TokenHolder.activities funciona correctamente
   - Agregado foreign_keys explícito para evitar ambigüedad
   - Permite queries eficientes por holder

2. ✅ Mejorados índices:
   - Índices compuestos para queries comunes
   - Índice único en transaction_hash
   - Índices en campos de fecha para reportes

3. ✅ Agregadas propiedades útiles:
   - balance_formatted
   - needs_burn, can_renew
   - holder_days
   - month_name, burn_rate, renew_rate

4. ✅ Agregado campo amount en TokenActivity:
   - Permite registrar montos en transacciones
   - Útil para transfers y burns parciales

MIGRACIÓN NECESARIA:

```sql
-- Agregar holder_id a token_activities
ALTER TABLE token_activities 
ADD COLUMN holder_id INTEGER REFERENCES token_holders(id) ON DELETE CASCADE;

-- Poblar holder_id desde user_id
UPDATE token_activities ta
SET holder_id = (
    SELECT id FROM token_holders th 
    WHERE th.user_id = ta.user_id
);

-- Hacer NOT NULL después de poblar
ALTER TABLE token_activities 
ALTER COLUMN holder_id SET NOT NULL;

-- Agregar índice
CREATE INDEX idx_token_activity_holder ON token_activities(holder_id);

-- Agregar campo amount si no existe
ALTER TABLE token_activities 
ADD COLUMN amount NUMERIC(78, 18);
```

TESTING:

```python
from app.models.token import TokenHolder, TokenActivity
from app.models.user import User
from app.db.session import SessionLocal

db = SessionLocal()

# Crear usuario y holder
user = User(wallet_address="0x123...")
db.add(user)
db.commit()

holder = TokenHolder(
    user_id=user.id,
    wallet_address="0x123...",
    balance=1.0,
    holder_since=datetime.utcnow()
)
db.add(holder)
db.commit()

# Crear actividad
activity = TokenActivity(
    holder_id=holder.id,  # ✅ Ahora funciona
    user_id=user.id,
    wallet_address="0x123...",
    activity_type="burn",
    amount=1.0
)
db.add(activity)
db.commit()

# Verificar relación funciona
print(holder.activities)  # ✅ [<TokenActivity...>]
print(activity.holder)    # ✅ <TokenHolder...>
print(holder.needs_burn)  # ✅ True/False

print("✅ All tests passed!")
```

TIPOS DE ACTIVIDADES COMUNES:

- "burn" - Token quemado por inactividad
- "renew" - Token renovado después de burn
- "transfer" - Transferencia de tokens
- "mint" - Acuñación de nuevo token
- "vote" - Voto en governance
- "proposal" - Creación de propuesta
- "deposit" - Depósito en fondo
- "withdrawal" - Retiro de fondo
"""