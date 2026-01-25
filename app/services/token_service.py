from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.token import TokenHolder, TokenActivity, TokenMonthlyStats
from app.models.user import User
from app.schemas.token import TokenActivityCreate, TokenStats
from app.services.base_service import BaseService
from app.core.enums import TokenActivityType
from app.core.helpers import days_until_burn, days_until_renew

logger = logging.getLogger(__name__)

class TokenService(BaseService[TokenHolder]):
    def __init__(self):
        super().__init__(TokenHolder)
    
    def get_holder(self, db: Session, wallet_address: str) -> Optional[TokenHolder]:
        return db.query(TokenHolder).filter(
            TokenHolder.wallet_address == wallet_address
        ).first()
    
    def create_holder(
        self,
        db: Session,
        user_id: int,
        wallet_address: str
    ) -> TokenHolder:
        existing = self.get_holder(db, wallet_address)
        if existing:
            raise ValueError("Token already minted for this address")
        
        holder = TokenHolder(
            user_id=user_id,
            wallet_address=wallet_address,
            balance=Decimal('1.0'),
            is_active=True,
            has_activity_this_month=True,
            holder_since=datetime.utcnow()
        )
        
        db.add(holder)
        db.commit()
        db.refresh(holder)
        self.record_activity(
            db=db,
            wallet_address=wallet_address,
            activity=TokenActivityCreate(
                activity_type=TokenActivityType.MINTED.value,
                description="GERAS token minted"
            )
        )
        logger.info(f"🪙 Token minted for {wallet_address}")
        return holder
    
    def record_activity(
        self,
        db: Session,
        wallet_address: str,
        activity: TokenActivityCreate
    ) -> TokenActivity:
        holder = self.get_holder(db, wallet_address)
        if not holder:
            raise ValueError("Token holder not found")

        holder.has_activity_this_month = True
        holder.last_activity_timestamp = datetime.utcnow()
        holder.last_activity_type = activity.activity_type
        activity_record = TokenActivity(
            user_id=holder.user_id,
            wallet_address=wallet_address,
            activity_type=activity.activity_type,
            description=activity.description,
            transaction_hash=activity.transaction_hash
        )
        db.add(activity_record)
        db.commit()
        db.refresh(activity_record)
        logger.info(f"📝 Activity recorded: {activity.activity_type} for {wallet_address}")
        return activity_record
    
    def get_holder_activities(
        self,
        db: Session,
        wallet_address: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[TokenActivity]:
        return db.query(TokenActivity).filter(
            TokenActivity.wallet_address == wallet_address
        ).order_by(desc(TokenActivity.created_at)).offset(skip).limit(limit).all()
    
    def get_all_holders(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[TokenHolder]:
        query = db.query(TokenHolder)
        if active_only:
            query = query.filter(TokenHolder.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    def get_inactive_holders(self, db: Session) -> List[TokenHolder]:
        return db.query(TokenHolder).filter(
            TokenHolder.is_active == True,
            TokenHolder.has_activity_this_month == False
        ).all()
    
    def get_stats(self, db: Session) -> TokenStats:
        total_holders = db.query(TokenHolder).count()
        active_holders = db.query(TokenHolder).filter(
            TokenHolder.is_active == True
        ).count()
        
        total_supply = db.query(TokenHolder).filter(
            TokenHolder.is_active == True
        ).count() 

        now = datetime.utcnow()
        current_stats = db.query(TokenMonthlyStats).filter(
            TokenMonthlyStats.year == now.year,
            TokenMonthlyStats.month == now.month
        ).first()
        
        return TokenStats(
            total_holders=total_holders,
            active_holders=active_holders,
            total_supply=Decimal(total_supply),
            current_month_burns=current_stats.holders_burned if current_stats else 0,
            current_month_renews=current_stats.holders_renewed if current_stats else 0
        )
    
    def get_burn_info(self, db: Session) -> Dict[str, Any]:
        days = days_until_burn()
        at_risk = self.get_inactive_holders(db)
        
        return {
            "days_until_burn": days,
            "burn_day": 28,
            "holders_at_risk": len(at_risk),
            "next_burn_date": (datetime.utcnow() + timedelta(days=days)).date()
        }
    
    def get_renew_info(self, db: Session) -> Dict[str, Any]:
        days = days_until_renew()
        active_holders = db.query(TokenHolder).filter(
            TokenHolder.is_active == True,
            TokenHolder.has_activity_this_month == True
        ).count()
        
        return {
            "days_until_renew": days,
            "renew_day": 1,
            "eligible_holders": active_holders,
            "next_renew_date": (datetime.utcnow() + timedelta(days=days)).date()
        }
    
    def reset_monthly_activity(self, db: Session):
        """Reset activity flags (called on renew day)"""
        db.query(TokenHolder).update({
            "has_activity_this_month": False,
            "burned_this_month": False,
            "renewed_this_month": False
        })
        db.commit()
        logger.info("🔄 Monthly activity flags reset")
    
    def sync_from_blockchain(self, db: Session) -> Dict[str, Any]:
        logger.info("🔄 Syncing token data from blockchain")
        return {"success": True, "message": "Sync initiated"}

token_service = TokenService()