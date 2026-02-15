from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, DECIMAL, 
    ForeignKey, Text, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# ---------------------------------------------------------------------------
# 📊 MODELO: Proposal
# ---------------------------------------------------------------------------

class Proposal(Base):
    """
    Modelo de Propuesta de Governance
    
    Almacena propuestas creadas para votación de governance del DAO.
    Cada propuesta tiene un período de votación y puede ser ejecutada
    o cancelada según los votos recibidos.
    """
    __tablename__ = "proposals"
    
    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Información del proposer
    proposer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    proposer_address = Column(String(42), nullable=False, index=True)
    
    # Contenido de la propuesta
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    proposal_type = Column(Integer, nullable=False, index=True)
    
    # Target para ejecución
    target_address = Column(String(42), nullable=True)
    target_value = Column(DECIMAL(18, 6), default=0, nullable=True)
    
    # Contadores de votos
    votes_for = Column(DECIMAL(78, 18), default=0, nullable=False)
    votes_against = Column(DECIMAL(78, 18), default=0, nullable=False)
    quorum_reached = Column(Boolean, default=False, nullable=False)
    
    # Tiempos de la propuesta
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    execution_time = Column(DateTime(timezone=True), nullable=False)
    
    # Estado
    executed = Column(Boolean, default=False, nullable=False, index=True)
    cancelled = Column(Boolean, default=False, nullable=False, index=True)
    
    # Información blockchain
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    proposer = relationship(
        "User", 
        back_populates="proposals",
        foreign_keys=[proposer_id]
    )
    
    # ✅ FIX: Agregado foreign_keys explícito para evitar ambigüedad
    votes = relationship(
        "Vote", 
        back_populates="proposal",
        foreign_keys="Vote.proposal_id",  # ← Especifica cuál FK usar
        cascade="all, delete-orphan"
    )
    
    # -------------------------------------------------------------------------
    # Índices y constraints
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_proposal_proposer', 'proposer_id'),
        Index('idx_proposal_status', 'executed', 'cancelled'),
        Index('idx_proposal_times', 'start_time', 'end_time'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos
    # -------------------------------------------------------------------------
    def __repr__(self):
        return f"<Proposal(id={self.proposal_id}, title={self.title[:30]})>"
    
    @property
    def is_active(self) -> bool:
        """Verifica si la propuesta está en período de votación"""
        from datetime import datetime
        now = datetime.utcnow()
        return (
            not self.executed and 
            not self.cancelled and 
            self.start_time <= now <= self.end_time
        )
    
    @property
    def total_votes(self) -> float:
        """Total de votos emitidos"""
        return float(self.votes_for + self.votes_against)
    
    @property
    def approval_percentage(self) -> float:
        """Porcentaje de aprobación"""
        total = self.total_votes
        if total == 0:
            return 0.0
        return (float(self.votes_for) / total) * 100

# ---------------------------------------------------------------------------
# 📊 MODELO: Vote
# ---------------------------------------------------------------------------

class Vote(Base):
    """
    Modelo de Voto
    
    Almacena votos individuales sobre propuestas.
    Cada usuario puede votar una sola vez por propuesta.
    """
    __tablename__ = "votes"
    
    # -------------------------------------------------------------------------
    # Campos principales
    # -------------------------------------------------------------------------
    id = Column(Integer, primary_key=True, index=True)
    
    # ✅ FIX CRÍTICO: Agregado ForeignKey que faltaba
    # ANTES: proposal_id = Column(Integer, nullable=False, index=True)
    # AHORA:
    proposal_id = Column(
        Integer, 
        ForeignKey('proposals.id', ondelete='CASCADE'),  # ← ForeignKey agregado
        nullable=False, 
        index=True
    )
    
    # Información del votante
    voter_id = Column(
        Integer, 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    voter_address = Column(String(42), nullable=False, index=True)
    
    # Información del voto
    support = Column(Boolean, nullable=False, index=True)  # True = A favor, False = En contra
    voting_power = Column(DECIMAL(78, 18), nullable=False)  # Poder de voto (balance de tokens)
    
    # Información blockchain
    transaction_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # -------------------------------------------------------------------------
    # Relaciones
    # -------------------------------------------------------------------------
    proposal = relationship(
        "Proposal", 
        back_populates="votes",
        foreign_keys=[proposal_id]
    )
    
    voter = relationship(
        "User", 
        back_populates="votes",
        foreign_keys=[voter_id]
    )
    
    # -------------------------------------------------------------------------
    # Índices y constraints
    # -------------------------------------------------------------------------
    __table_args__ = (
        # Un usuario solo puede votar una vez por propuesta
        UniqueConstraint('proposal_id', 'voter_id', name='uq_proposal_voter'),
        
        # Índices compuestos para queries comunes
        Index('idx_vote_proposal', 'proposal_id'),
        Index('idx_vote_voter', 'voter_id'),
        Index('idx_vote_support', 'support'),
        Index('idx_vote_proposal_support', 'proposal_id', 'support'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos
    # -------------------------------------------------------------------------
    def __repr__(self):
        vote_type = "FOR" if self.support else "AGAINST"
        return (
            f"<Vote(proposal_id={self.proposal_id}, "
            f"voter_id={self.voter_id}, "
            f"{vote_type})>"
        )
    
    @property
    def vote_type_text(self) -> str:
        """Texto legible del tipo de voto"""
        return "For" if self.support else "Against"

# ---------------------------------------------------------------------------
# 📊 MODELO: VoterStats
# ---------------------------------------------------------------------------

class VoterStats(Base):
    """
    Modelo de Estadísticas de Votante
    
    Almacena estadísticas agregadas de participación en governance
    para cada usuario. Se actualiza cada vez que un usuario vota
    o crea una propuesta.
    """
    __tablename__ = "voter_stats"
    
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
    voter_address = Column(String(42), nullable=False, index=True)
    
    # Contadores
    total_votes_cast = Column(Integer, default=0, nullable=False)
    proposals_created = Column(Integer, default=0, nullable=False)
    votes_for_count = Column(Integer, default=0, nullable=False)
    votes_against_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps de última actividad
    last_vote_at = Column(DateTime(timezone=True), nullable=True)
    last_proposal_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps del registro
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
        back_populates="voter_stats",
        foreign_keys=[user_id]
    )
    
    # -------------------------------------------------------------------------
    # Índices
    # -------------------------------------------------------------------------
    __table_args__ = (
        Index('idx_voter_stats_user', 'user_id'),
        Index('idx_voter_stats_address', 'voter_address'),
        Index('idx_voter_stats_participation', 'total_votes_cast'),
    )
    
    # -------------------------------------------------------------------------
    # Métodos y propiedades
    # -------------------------------------------------------------------------
    def __repr__(self):
        return (
            f"<VoterStats(user_id={self.user_id}, "
            f"votes={self.total_votes_cast}, "
            f"proposals={self.proposals_created})>"
        )
    
    @property
    def participation_rate(self) -> float:
        """
        Tasa de participación (total de votos)
        Nota: Para calcular % real necesitarías total de propuestas disponibles
        """
        return float(self.total_votes_cast)
    
    @property
    def approval_ratio(self) -> float:
        """Porcentaje de votos a favor vs total de votos"""
        if self.total_votes_cast == 0:
            return 0.0
        return (self.votes_for_count / self.total_votes_cast) * 100
    
    @property
    def is_active_voter(self) -> bool:
        """Verifica si el usuario ha votado recientemente (último mes)"""
        if not self.last_vote_at:
            return False
        
        from datetime import datetime, timedelta
        one_month_ago = datetime.utcnow() - timedelta(days=30)
        return self.last_vote_at >= one_month_ago
    
    @property
    def is_proposal_creator(self) -> bool:
        """Verifica si el usuario ha creado propuestas"""
        return self.proposals_created > 0


"""
CAMBIOS REALIZADOS:


TESTING POST-FIX:

Para verificar que el fix funciona:

```python
# En Python shell o script
from app.models.governance import Proposal, Vote
from app.db.session import SessionLocal

db = SessionLocal()

# Debe funcionar sin error
proposal = Proposal(
    proposal_id=1,
    proposer_address="0x...",
    title="Test",
    description="Test proposal",
    # ... otros campos
)
db.add(proposal)
db.commit()

# Debe poder crear votos relacionados
vote = Vote(
    proposal_id=proposal.id,  # ← Ahora funciona correctamente
    voter_id=1,
    voter_address="0x...",
    support=True,
    voting_power=100
)
db.add(vote)
db.commit()

print("✅ Fix verified!")
```

MIGRACIÓN DE BASE DE DATOS:

Si ya tienes datos en producción, necesitarás:

```sql
-- Agregar el foreign key a la tabla existente
ALTER TABLE votes 
ADD CONSTRAINT fk_votes_proposal_id 
FOREIGN KEY (proposal_id) 
REFERENCES proposals(id) 
ON DELETE CASCADE;

-- Verificar que se creó correctamente
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE table_name = 'votes' 
AND constraint_type = 'FOREIGN KEY';
```
"""