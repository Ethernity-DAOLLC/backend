from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.governance import Proposal, Vote, VoterStats
from app.models.token import TokenHolder
from app.models.user import User
from app.schemas.governance import ProposalCreate, ProposalStats, VoterStatsResponse
from app.services.base_service import BaseService
from app.core.enums import ProposalType, ProposalStatus
from app.core.helpers import get_proposal_status

logger = logging.getLogger(__name__)

class GovernanceService(BaseService[Proposal]):
    def __init__(self):
        super().__init__(Proposal)
    
    def create_proposal(
        self,
        db: Session,
        wallet_address: str,
        proposal_data: ProposalCreate
    ) -> Proposal:
        holder = db.query(TokenHolder).filter(
            TokenHolder.wallet_address == wallet_address,
            TokenHolder.is_active == True
        ).first()
        
        if not holder:
            raise ValueError("Must be an active token holder to create proposals")
        
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        last_proposal = db.query(Proposal).order_by(
            desc(Proposal.proposal_id)
        ).first()
        next_id = (last_proposal.proposal_id + 1) if last_proposal else 1

        start_time = datetime.utcnow() + timedelta(days=1)  # 1 day delay
        end_time = start_time + timedelta(days=3)  # 3 day voting period
        execution_time = end_time + timedelta(days=2)  # 2 day timelock
        
        proposal = Proposal(
            proposal_id=next_id,
            proposer_id=user.id if user else None,
            proposer_address=wallet_address,
            title=proposal_data.title,
            description=proposal_data.description,
            proposal_type=proposal_data.proposal_type,
            target_address=proposal_data.target_address,
            target_value=proposal_data.target_value,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            transaction_hash="0x" + "0" * 64  
        )
        
        db.add(proposal)
        stats = db.query(VoterStats).filter(
            VoterStats.user_id == user.id
        ).first() if user else None
        
        if stats:
            stats.proposals_created += 1
        elif user:
            stats = VoterStats(user_id=user.id, proposals_created=1)
            db.add(stats)
        db.commit()
        db.refresh(proposal)
        logger.info(f"📜 Proposal created: #{proposal.proposal_id} by {wallet_address}")
        return proposal
    
    def get_proposals(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        proposal_type: Optional[int] = None
    ) -> List[Proposal]:
        query = db.query(Proposal)
        if proposal_type is not None:
            query = query.filter(Proposal.proposal_type == proposal_type)
        if status:
            if status == ProposalStatus.ACTIVE.value:
                query = query.filter(
                    Proposal.start_time <= datetime.utcnow(),
                    Proposal.end_time >= datetime.utcnow(),
                    Proposal.executed == False,
                    Proposal.cancelled == False
                )
            elif status == ProposalStatus.EXECUTED.value:
                query = query.filter(Proposal.executed == True)
            elif status == ProposalStatus.CANCELLED.value:
                query = query.filter(Proposal.cancelled == True)
        return query.order_by(desc(Proposal.created_at)).offset(skip).limit(limit).all()
    
    def get_proposal(self, db: Session, proposal_id: int) -> Optional[Proposal]:
        return db.query(Proposal).filter(
            Proposal.proposal_id == proposal_id
        ).first()
    
    def get_active_proposals(self, db: Session) -> List[Proposal]:
        now = datetime.utcnow()
        return db.query(Proposal).filter(
            Proposal.start_time <= now,
            Proposal.end_time >= now,
            Proposal.executed == False,
            Proposal.cancelled == False
        ).all()
    
    def get_pending_execution(self, db: Session) -> List[Proposal]:
        now = datetime.utcnow()
        return db.query(Proposal).filter(
            Proposal.end_time < now,
            Proposal.execution_time <= now,
            Proposal.executed == False,
            Proposal.cancelled == False,
            Proposal.votes_for > Proposal.votes_against,
            Proposal.quorum_reached == True
        ).all()
    
    def cast_vote(
        self,
        db: Session,
        proposal_id: int,
        wallet_address: str,
        support: bool
    ) -> Vote:
        proposal = self.get_proposal(db, proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        now = datetime.utcnow()
        if now < proposal.start_time:
            raise ValueError("Voting has not started")
        if now > proposal.end_time:
            raise ValueError("Voting has ended")
        if proposal.cancelled:
            raise ValueError("Proposal is cancelled")
        if proposal.executed:
            raise ValueError("Proposal already executed")
        holder = db.query(TokenHolder).filter(
            TokenHolder.wallet_address == wallet_address,
            TokenHolder.is_active == True
        ).first()
        
        if not holder:
            raise ValueError("Must hold active GERAS token to vote")
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        existing_vote = db.query(Vote).filter(
            Vote.proposal_id == proposal_id,
            Vote.voter_id == user.id
        ).first() if user else None
        
        if existing_vote:
            raise ValueError("Already voted on this proposal")

        voting_power = holder.balance
        vote = Vote(
            proposal_id=proposal_id,
            voter_id=user.id if user else None,
            voter_address=wallet_address,
            support=support,
            voting_power=voting_power,
            transaction_hash="0x" + "0" * 64, 
            block_timestamp=datetime.utcnow()
        )

        if support:
            proposal.votes_for += voting_power
        else:
            proposal.votes_against += voting_power
        total_votes = proposal.votes_for + proposal.votes_against
        total_supply = db.query(TokenHolder).filter(
            TokenHolder.is_active == True
        ).count()
        
        if total_supply > 0:
            required_votes = total_supply * 0.2 
            if total_votes >= required_votes:
                proposal.quorum_reached = True
        
        db.add(vote)
        if user:
            stats = db.query(VoterStats).filter(
                VoterStats.user_id == user.id
            ).first()
            if stats:
                stats.total_votes_cast += 1
                stats.last_vote_timestamp = datetime.utcnow()
            else:
                stats = VoterStats(
                    user_id=user.id,
                    total_votes_cast=1,
                    last_vote_timestamp=datetime.utcnow()
                )
                db.add(stats)
        db.commit()
        db.refresh(vote)
        logger.info(f"🗳️ Vote cast on proposal #{proposal_id}: {'FOR' if support else 'AGAINST'}")
        return vote
    
    def can_vote(
        self,
        db: Session,
        proposal_id: int,
        wallet_address: str
    ) -> Dict[str, Any]:
        proposal = self.get_proposal(db, proposal_id)
        if not proposal:
            return {"can_vote": False, "reason": "Proposal not found"}
        now = datetime.utcnow()
        if now < proposal.start_time:
            return {"can_vote": False, "reason": "Voting not started"}
        if now > proposal.end_time:
            return {"can_vote": False, "reason": "Voting ended"}
        if proposal.cancelled:
            return {"can_vote": False, "reason": "Proposal cancelled"}
        if proposal.executed:
            return {"can_vote": False, "reason": "Proposal executed"}
        holder = db.query(TokenHolder).filter(
            TokenHolder.wallet_address == wallet_address,
            TokenHolder.is_active == True
        ).first()
        
        if not holder:
            return {"can_vote": False, "reason": "Not a token holder"}
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if user:
            existing_vote = db.query(Vote).filter(
                Vote.proposal_id == proposal_id,
                Vote.voter_id == user.id
            ).first()
            if existing_vote:
                return {"can_vote": False, "reason": "Already voted"}
        return {"can_vote": True, "voting_power": float(holder.balance)}
    
    def get_proposal_votes(
        self,
        db: Session,
        proposal_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Vote]:
        return db.query(Vote).filter(
            Vote.proposal_id == proposal_id
        ).order_by(desc(Vote.created_at)).offset(skip).limit(limit).all()
    
    def execute_proposal(
        self,
        db: Session,
        proposal_id: int,
        transaction_hash: str
    ) -> Dict[str, Any]:
        proposal = self.get_proposal(db, proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        if proposal.executed:
            raise ValueError("Proposal already executed")
        if proposal.cancelled:
            raise ValueError("Proposal is cancelled")
        now = datetime.utcnow()
        if now <= proposal.end_time:
            raise ValueError("Voting not finished")
        if now < proposal.execution_time:
            raise ValueError("Execution timelock not expired")
        if proposal.votes_for <= proposal.votes_against:
            raise ValueError("Proposal not approved")
        if not proposal.quorum_reached:
            raise ValueError("Quorum not reached")
        
        proposal.executed = True
        proposal.executed_at = datetime.utcnow()
        db.commit()
        logger.info(f"✅ Proposal #{proposal_id} executed")
        return {"success": True, "proposal_id": proposal_id}
    
    def cancel_proposal(
        self,
        db: Session,
        proposal_id: int,
        wallet_address: str,
        reason: str
    ) -> Dict[str, Any]:
        proposal = self.get_proposal(db, proposal_id)
        if not proposal:
            raise ValueError("Proposal not found")
        if proposal.cancelled:
            raise ValueError("Already cancelled")
        if proposal.executed:
            raise ValueError("Already executed")
        if wallet_address == proposal.proposer_address:
            if datetime.utcnow() >= proposal.start_time:
                raise ValueError("Proposer can only cancel before voting starts")
        else:
            pass
        
        proposal.cancelled = True
        proposal.cancelled_at = datetime.utcnow()
        db.commit()
        logger.info(f"❌ Proposal #{proposal_id} cancelled: {reason}")
        return {"success": True, "proposal_id": proposal_id}
    
    def get_stats(self, db: Session) -> ProposalStats:
        total_proposals = db.query(Proposal).count()
        active_proposals = len(self.get_active_proposals(db))
        executed_proposals = db.query(Proposal).filter(
            Proposal.executed == True
        ).count()
        total_votes = db.query(Vote).count()
        
        return ProposalStats(
            total_proposals=total_proposals,
            active_proposals=active_proposals,
            executed_proposals=executed_proposals,
            total_votes=total_votes
        )
    
    def get_voter_stats(
        self,
        db: Session,
        wallet_address: str
    ) -> Optional[VoterStatsResponse]:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return None
        
        stats = db.query(VoterStats).filter(VoterStats.user_id == user.id).first()
        if not stats:
            return VoterStatsResponse(
                total_votes_cast=0,
                proposals_created=0,
                last_vote_timestamp=None
            )
        
        return VoterStatsResponse(
            total_votes_cast=stats.total_votes_cast,
            proposals_created=stats.proposals_created,
            last_vote_timestamp=stats.last_vote_timestamp
        )
    
    async def notify_new_proposal(self, proposal_id: int):
        logger.info(f"📢 Notifying holders about proposal #{proposal_id}")
    
    async def check_quorum_and_notify(self, proposal_id: int):
        logger.info(f"📊 Checking quorum for proposal #{proposal_id}")

governance_service = GovernanceService()