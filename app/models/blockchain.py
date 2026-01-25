from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.base_class import Base

class BlockchainEvent(Base):
    __tablename__ = "blockchain_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(Integer, nullable=False, index=True)
    block_timestamp = Column(DateTime(timezone=True), nullable=False)
    log_index = Column(Integer, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint('transaction_hash', 'log_index', name='uq_tx_log'),
    )