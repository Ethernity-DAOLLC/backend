from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=128)
    description: str = Field(..., min_length=10, max_length=512)
    proposal_type: int = Field(..., ge=0, le=3)
    target_address: Optional[str] = Field(None, pattern=r'^0x[a-fA-F0-9]{40}$')
    target_value: Decimal = Field(default=0, ge=0)

class ProposalResponse(BaseModel):
    id: int
    proposal_id: int
    proposer_address: str
    title: str
    description: str
    proposal_type: int
    votes_for: Decimal
    votes_against: Decimal
    quorum_reached: bool
    start_time: datetime
    end_time: datetime
    execution_time: datetime
    executed: bool
    cancelled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    proposal_id: int
    support: bool

class VoteResponse(BaseModel):
    id: int
    proposal_id: int
    voter_address: str
    support: bool
    voting_power: Decimal
    block_timestamp: datetime
    
    class Config:
        from_attributes = True

class ProposalStats(BaseModel):
    total_proposals: int
    active_proposals: int
    executed_proposals: int
    total_votes: int

class VoterStatsResponse(BaseModel):
    total_votes_cast: int
    proposals_created: int
    last_vote_timestamp: Optional[datetime]