from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.personal_fund import PersonalFund
from app.models.token import TokenHolder
from app.models.governance import Proposal, Vote
from app.models.analytics import DailySnapshot
from app.models.user import User
from app.schemas.analytics import (
    UserDashboard, FundPerformance, SystemHealthCheck
)
from app.services.base_service import BaseService
from app.core.helpers import get_fund_status

logger = logging.getLogger(__name__)

class AnalyticsService(BaseService[DailySnapshot]):
    def __init__(self):
        super().__init__(DailySnapshot)
    
    def get_user_dashboard(self, db: Session, wallet_address: str) -> Optional[UserDashboard]:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return None

        token_holder = db.query(TokenHolder).filter(
            TokenHolder.user_id == user.id
        ).first()
        fund = db.query(PersonalFund).filter(
            PersonalFund.owner_id == user.id
        ).first()
        vote_count = db.query(Vote).filter(Vote.voter_id == user.id).count()
        proposal_count = db.query(Proposal).filter(
            Proposal.proposer_id == user.id
        ).count()
        
        return UserDashboard(
            wallet_address=wallet_address,
            has_fund=fund is not None,
            fund_address=fund.fund_address if fund else None,
            fund_balance=fund.total_balance if fund else None,
            retirement_status=get_fund_status(
                fund.retirement_started,
                fund.early_retirement_approved,
                fund.timelock_end
            ) if fund else None,
            is_token_holder=token_holder is not None,
            token_balance=token_holder.balance if token_holder else None,
            has_activity_this_month=token_holder.has_activity_this_month if token_holder else False,
            total_votes_cast=vote_count,
            proposals_created=proposal_count,
            last_activity=token_holder.last_activity_timestamp if token_holder else user.last_login
        )
    
    def get_fund_performance(self, db: Session, fund_id: int) -> Optional[FundPerformance]:
        fund = db.query(PersonalFund).filter(PersonalFund.id == fund_id).first()
        if not fund:
            return None
        
        initial_deposit = fund.principal + fund.monthly_deposit
        total_return = fund.total_balance - fund.total_gross_deposited + fund.total_withdrawn
        return_pct = (
            (total_return / fund.total_gross_deposited * 100) 
            if fund.total_gross_deposited > 0 else 0
        )
        days_active = (datetime.utcnow() - fund.created_at).days
        
        return FundPerformance(
            fund_address=fund.fund_address,
            owner_address=fund.owner_address,
            initial_deposit=initial_deposit,
            total_deposited=fund.total_gross_deposited,
            current_balance=fund.total_balance,
            total_return=total_return,
            return_percentage=float(return_pct),
            days_active=days_active,
            monthly_deposits_made=fund.monthly_deposit_count
        )
    
    def get_snapshots(
        self,
        db: Session,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 30
    ) -> List[DailySnapshot]:
        query = db.query(DailySnapshot)
        if from_date:
            query = query.filter(DailySnapshot.snapshot_date >= from_date)
        if to_date:
            query = query.filter(DailySnapshot.snapshot_date <= to_date)
        return query.order_by(
            desc(DailySnapshot.snapshot_date)
        ).limit(limit).all()
    
    def create_snapshot(self, db: Session) -> DailySnapshot:
        today = date.today()
        existing = db.query(DailySnapshot).filter(
            DailySnapshot.snapshot_date == today
        ).first()
        if existing:
            logger.warning(f"Snapshot already exists for {today}")
            return existing

        total_holders = db.query(TokenHolder).count()
        active_holders = db.query(TokenHolder).filter(
            TokenHolder.is_active == True
        ).count()
        total_funds = db.query(PersonalFund).count()
        active_funds = db.query(PersonalFund).filter(
            PersonalFund.initialized == True
        ).count()
        funds_in_retirement = db.query(PersonalFund).filter(
            PersonalFund.retirement_started == True
        ).count()
        
        active_proposals = db.query(Proposal).filter(
            Proposal.start_time <= datetime.utcnow(),
            Proposal.end_time >= datetime.utcnow(),
            Proposal.executed == False,
            Proposal.cancelled == False
        ).count()
        total_tvl = db.query(func.sum(PersonalFund.total_balance)).scalar() or Decimal(0)
        snapshot = DailySnapshot(
            snapshot_date=today,
            total_token_holders=total_holders,
            active_token_holders=active_holders,
            total_funds=total_funds,
            active_funds=active_funds,
            funds_in_retirement=funds_in_retirement,
            total_deposits_today=Decimal(0), 
            total_withdrawals_today=Decimal(0),
            total_fees_today=Decimal(0),
            total_tvl=total_tvl,
            active_proposals=active_proposals,
            votes_cast_today=0
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        logger.info(f"📊 Daily snapshot created for {today}")
        return snapshot
    
    def health_check(self, db: Session) -> SystemHealthCheck:
        try:
            db.execute("SELECT 1")
            db_healthy = True
        except:
            db_healthy = False
        last_event = db.query(BlockchainEvent).order_by(
            desc(BlockchainEvent.block_number)
        ).first()
        unprocessed = db.query(BlockchainEvent).filter(
            BlockchainEvent.processed == False
        ).count()
        active_funds = db.query(PersonalFund).filter(
            PersonalFund.initialized == True
        ).count()
        total_tvl = db.query(func.sum(PersonalFund.total_balance)).scalar() or Decimal(0)
        return SystemHealthCheck(
            database_healthy=db_healthy,
            blockchain_synced=unprocessed < 100,
            last_block_processed=last_event.block_number if last_event else 0,
            pending_events=unprocessed,
            active_funds=active_funds,
            total_tvl=total_tvl,
            timestamp=datetime.utcnow()
        )
    
    def get_system_metrics(self, db: Session) -> Dict[str, Any]:
        return {
            "funds": {
                "total": db.query(PersonalFund).count(),
                "active": db.query(PersonalFund).filter(PersonalFund.initialized == True).count(),
                "in_retirement": db.query(PersonalFund).filter(PersonalFund.retirement_started == True).count()
            },
            "tokens": {
                "total_holders": db.query(TokenHolder).count(),
                "active_holders": db.query(TokenHolder).filter(TokenHolder.is_active == True).count()
            },
            "governance": {
                "total_proposals": db.query(Proposal).count(),
                "active_proposals": db.query(Proposal).filter(
                    Proposal.executed == False,
                    Proposal.cancelled == False
                ).count(),
                "total_votes": db.query(Vote).count()
            }
        }
    
    def get_top_funds(self, db: Session, limit: int = 10) -> List[FundPerformance]:
        funds = db.query(PersonalFund).order_by(
            desc(PersonalFund.total_balance)
        ).limit(limit).all()
        return [self.get_fund_performance(db, f.id) for f in funds]

analytics_service = AnalyticsService()
