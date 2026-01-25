from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.treasury import (
    TreasuryStats, FundFeeRecord,
    EarlyRetirementRequest, TreasuryWithdrawal
)
from app.models.personal_fund import PersonalFund
from app.models.user import User
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

class TreasuryService(BaseService[EarlyRetirementRequest]):
    def __init__(self):
        super().__init__(EarlyRetirementRequest)
    
    def create_early_retirement_request(
        self,
        db: Session,
        wallet_address: str,
        fund_address: str,
        reason: str
    ) -> EarlyRetirementRequest:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            raise ValueError("User not found")
        
        fund = db.query(PersonalFund).filter(
            PersonalFund.fund_address == fund_address,
            PersonalFund.owner_id == user.id
        ).first()
        
        if not fund:
            raise ValueError("Fund not found or not owned by user")
        if fund.retirement_started:
            raise ValueError("Fund already in retirement")
        existing = db.query(EarlyRetirementRequest).filter(
            EarlyRetirementRequest.fund_id == fund.id,
            EarlyRetirementRequest.processed == False
        ).first()
        
        if existing:
            raise ValueError("Pending early retirement request already exists")
        
        request = EarlyRetirementRequest(
            fund_id=fund.id,
            fund_address=fund_address,
            requester_id=user.id,
            requester_address=wallet_address,
            reason=reason,
            request_timestamp=datetime.utcnow()
        )
        
        db.add(request)
        db.commit()
        db.refresh(request)
        logger.info(f"📝 Early retirement requested for fund {fund_address}")
        return request
    
    def get_request_by_fund(
        self,
        db: Session,
        fund_address: str
    ) -> Optional[EarlyRetirementRequest]:
        return db.query(EarlyRetirementRequest).filter(
            EarlyRetirementRequest.fund_address == fund_address
        ).first()
    
    def get_all_requests(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        pending_only: bool = False
    ) -> List[EarlyRetirementRequest]:
        query = db.query(EarlyRetirementRequest)
        if pending_only:
            query = query.filter(EarlyRetirementRequest.processed == False)
        return query.order_by(
            desc(EarlyRetirementRequest.request_timestamp)
        ).offset(skip).limit(limit).all()
    
    def approve_direct(
        self,
        db: Session,
        request_id: int,
        transaction_hash: str
    ) -> Dict[str, Any]:
        request = self.get(db, request_id)
        if not request:
            raise ValueError("Request not found")
        if request.processed:
            raise ValueError("Request already processed")
        request.approved = True
        request.processed = True
        request.processed_timestamp = datetime.utcnow()
        fund = db.query(PersonalFund).filter(
            PersonalFund.id == request.fund_id
        ).first()
        
        if fund:
            fund.early_retirement_approved = True
        db.commit()
        logger.info(f"✅ Early retirement approved for fund {request.fund_address}")
        return {"success": True, "request_id": request_id}
    
    def reject_request(
        self,
        db: Session,
        request_id: int,
        reason: str
    ) -> Dict[str, Any]:
        request = self.get(db, request_id)
        if not request:
            raise ValueError("Request not found")
        if request.processed:
            raise ValueError("Request already processed")
        
        request.rejected = True
        request.processed = True
        request.processed_timestamp = datetime.utcnow()
        db.commit()
        logger.info(f"❌ Early retirement rejected for fund {request.fund_address}")
        return {"success": True, "request_id": request_id, "reason": reason}
    
    def get_stats(self, db: Session) -> TreasuryStats:
        stats = db.query(TreasuryStats).first()
        if not stats:
            stats = TreasuryStats()
            db.add(stats)
            db.commit()
            db.refresh(stats)
        return stats
    
    def get_fund_fees(self, db: Session, fund_address: str) -> Optional[FundFeeRecord]:
        return db.query(FundFeeRecord).filter(
            FundFeeRecord.fund_address == fund_address
        ).first()
    
    def get_all_fees(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[FundFeeRecord]:
        return db.query(FundFeeRecord).order_by(
            desc(FundFeeRecord.total_fees_paid)
        ).offset(skip).limit(limit).all()
    
    def record_fee(
        self,
        db: Session,
        fund_address: str,
        amount: float,
        transaction_hash: str
    ) -> Dict[str, Any]:
        fee_record = self.get_fund_fees(db, fund_address)
        
        if not fee_record:
            fund = db.query(PersonalFund).filter(
                PersonalFund.fund_address == fund_address
            ).first()
            
            if not fund:
                raise ValueError("Fund not found")
            fee_record = FundFeeRecord(
                fund_id=fund.id,
                fund_address=fund_address,
                total_fees_paid=Decimal(0),
                fee_count=0
            )
            db.add(fee_record)
        
        fee_record.total_fees_paid += Decimal(str(amount))
        fee_record.fee_count += 1
        fee_record.last_fee_timestamp = datetime.utcnow()
        stats = self.get_stats(db)
        stats.total_fees_collected_usdc += Decimal(str(amount))
        stats.total_fees_collected_all_time += Decimal(str(amount))
        db.commit()
        logger.info(f"💰 Fee recorded: {amount} USDC from {fund_address}")
        return {"success": True, "amount": amount}
    
    async def notify_early_retirement_request(self, request_id: int):
        logger.info(f"📢 Notifying about early retirement request #{request_id}")

treasury_service = TreasuryService()