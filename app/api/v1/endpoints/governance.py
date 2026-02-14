from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.api.deps import get_db, get_current_admin
from app.schemas.governance import (
    ProposalCreate,
    ProposalResponse,
    VoteCreate,
    VoteResponse,
    ProposalStats,
    VoterStatsResponse
)
from app.services.governance_service import governance_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new proposal"
)
async def create_proposal(
    wallet_address: str,
    proposal_data: ProposalCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    try:
        proposal = governance_service.create_proposal(
            db=db,
            wallet_address=wallet_address,
            proposal_data=proposal_data
        )

        background_tasks.add_task(
            governance_service.notify_new_proposal,
            proposal.id
        )
        return proposal
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/proposals",
    response_model=List[ProposalResponse],
    summary="Get all proposals"
)
async def get_proposals(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    proposal_type: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return governance_service.get_proposals(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        proposal_type=proposal_type
    )

@router.get(
    "/proposals/{proposal_id}",
    response_model=ProposalResponse,
    summary="Get proposal by ID"
)
async def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db)
):
    proposal = governance_service.get_proposal(db, proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    return proposal

@router.get(
    "/proposals/active",
    response_model=List[ProposalResponse],
    summary="Get active proposals"
)
async def get_active_proposals(db: Session = Depends(get_db)):
    return governance_service.get_active_proposals(db)

@router.get(
    "/proposals/pending-execution",
    response_model=List[ProposalResponse],
    summary="Get proposals pending execution"
)
async def get_pending_execution(db: Session = Depends(get_db)):
    return governance_service.get_pending_execution(db)

@router.post(
    "/proposals/{proposal_id}/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vote on proposal"
)
async def vote_on_proposal(
    proposal_id: int,
    wallet_address: str,
    vote_data: VoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    try:
        vote = governance_service.cast_vote(
            db=db,
            proposal_id=proposal_id,
            wallet_address=wallet_address,
            support=vote_data.support
        )

        background_tasks.add_task(
            governance_service.check_quorum_and_notify,
            proposal_id
        )
        return vote
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/proposals/{proposal_id}/votes",
    response_model=List[VoteResponse],
    summary="Get votes for proposal"
)
async def get_proposal_votes(
    proposal_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return governance_service.get_proposal_votes(
        db=db,
        proposal_id=proposal_id,
        skip=skip,
        limit=limit
    )

@router.get(
    "/proposals/{proposal_id}/can-vote/{wallet_address}",
    summary="Check if user can vote"
)
async def can_vote(
    proposal_id: int,
    wallet_address: str,
    db: Session = Depends(get_db)
):
    result = governance_service.can_vote(
        db=db,
        proposal_id=proposal_id,
        wallet_address=wallet_address
    )
    return result

@router.post(
    "/proposals/{proposal_id}/execute",
    summary="Execute proposal (Admin)",
    dependencies=[Depends(get_current_admin)]
)
async def execute_proposal(
    proposal_id: int,
    transaction_hash: str,
    db: Session = Depends(get_db)
):
    try:
        result = governance_service.execute_proposal(
            db=db,
            proposal_id=proposal_id,
            transaction_hash=transaction_hash
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post(
    "/proposals/{proposal_id}/cancel",
    summary="Cancel proposal"
)
async def cancel_proposal(
    proposal_id: int,
    wallet_address: str,
    reason: str,
    db: Session = Depends(get_db)
):
    try:
        result = governance_service.cancel_proposal(
            db=db,
            proposal_id=proposal_id,
            wallet_address=wallet_address,
            reason=reason
        )
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/stats",
    response_model=ProposalStats,
    summary="Get governance statistics"
)
async def get_governance_stats(db: Session = Depends(get_db)):
    return governance_service.get_stats(db)

@router.get(
    "/voter/{wallet_address}/stats",
    response_model=VoterStatsResponse,
    summary="Get voter statistics"
)
async def get_voter_stats(
    wallet_address: str,
    db: Session = Depends(get_db)
):
    stats = governance_service.get_voter_stats(db, wallet_address)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voter not found"
        )
    return stats
