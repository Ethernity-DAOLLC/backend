from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Proposal(Base):
    __tablename__ = "proposals"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, unique=True, nullable=False, index=True)
    proposer_id = Column(Integer, ForeignKey('users.id'))
    proposer_address = Column(String(42), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    proposal_type = Column(Integer, nullable=False, index=True)
    target_address = Column(String(42))
    target_value = Column(DECIMAL(18, 6), default=0)
    votes_for = Column(DECIMAL(78, 18), default=0)
    votes_against = Column(DECIMAL(78, 18), default=0)
    quorum_reached = Column(Boolean, default=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    execution_time = Column(DateTime(timezone=True), nullable=False)
    executed = Column(Boolean, default=False, index=True)
    cancelled = Column(Boolean, default=False, index=True)
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    proposer = relationship("User", back_populates="proposals")
    votes = relationship("Vote", back_populates="proposal", cascade="all, delete-orphan")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, nullable=False, index=True)
    voter_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    voter_address = Column(String(42), nullable=False)
    support = Column(Boolean, nullable=False, index=True)
    voting_power = Column(DECIMAL(78, 18), nullable=False)
    transaction_hash = Column(String(66), nullable=False)
    block_number = Column(Integer, nullable=False)
    block_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    proposal = relationship("Proposal", back_populates="votes")
    voter = relationship("User", back_populates="votes")
    __table_args__ = (
        UniqueConstraint('proposal_id', 'voter_id', name='uq_proposal_voter'),
    )
