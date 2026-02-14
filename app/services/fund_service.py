from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.personal_fund import PersonalFund, FundTransaction, FundInvestment
from app.models.user import User
from app.schemas.fund import (
    PersonalFundCreate, FundBalances, FundStats,
    AutoWithdrawalConfig, AutoWithdrawalInfo
)
from app.services.base_service import BaseService
from app.core.enums import FundStatus, FundTransactionType
from app.core.helpers import get_fund_status

logger = logging.getLogger(__name__)

class FundService(BaseService[PersonalFund]):
    def __init__(self):
        super().__init__(PersonalFund)
    
    def get_by_wallet(self, db: Session, wallet_address: str) -> Optional[PersonalFund]:
        return db.query(PersonalFund).join(User).filter(
            User.wallet_address == wallet_address
        ).first()
    
    def get_by_address(self, db: Session, fund_address: str) -> Optional[PersonalFund]:
        return db.query(PersonalFund).filter(
            PersonalFund.fund_address == fund_address
        ).first()
    
    def create_fund(
        self,
        db: Session,
        wallet_address: str,
        fund_data: PersonalFundCreate,
        client_info: Optional[Dict] = None
    ) -> PersonalFund:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            raise ValueError("User not found")
        existing = self.get_by_wallet(db, wallet_address)
        if existing:
            raise ValueError("User already has a personal fund")
        timelock_seconds = fund_data.timelock_years * 365 * 86400
        timelock_end = datetime.utcnow() + timedelta(seconds=timelock_seconds)
        fund = PersonalFund(
            owner_id=user.id,
            owner_address=wallet_address,
            fund_address="", 
            principal=fund_data.principal,
            monthly_deposit=fund_data.monthly_deposit,
            current_age=fund_data.current_age,
            retirement_age=fund_data.retirement_age,
            desired_monthly=fund_data.desired_monthly,
            years_payments=fund_data.years_payments,
            interest_rate=fund_data.interest_rate,
            timelock_period=timelock_seconds,
            timelock_end=timelock_end,
            initialized=False
        )
        
        db.add(fund)
        db.commit()
        db.refresh(fund)
        logger.info(f"✅ Fund created for {wallet_address} - ID: {fund.id}")
        return fund
    
    def complete_fund_creation(
        self,
        db: Session,
        fund_id: int,
        fund_address: str,
        transaction_hash: str
    ) -> PersonalFund:
        fund = self.get(db, fund_id)
        if not fund:
            raise ValueError("Fund not found")
        fund.fund_address = fund_address
        fund.initialized = True
        initial_deposit = fund.principal + fund.monthly_deposit
        fee_amount = self._calculate_fee(initial_deposit)
        net_amount = initial_deposit - fee_amount
        transaction = FundTransaction(
            fund_id=fund.id,
            fund_address=fund_address,
            transaction_type=FundTransactionType.INITIAL_DEPOSIT.value,
            gross_amount=initial_deposit,
            fee_amount=fee_amount,
            net_amount=net_amount,
            transaction_hash=transaction_hash,
            block_number=0,  
            block_timestamp=datetime.utcnow()
        )
        
        fund.total_gross_deposited = initial_deposit
        fund.total_fees_paid = fee_amount
        fund.total_net_to_fund = net_amount
        fund.total_balance = net_amount
        fund.available_balance = net_amount
        fund.monthly_deposit_count = 1
        db.add(transaction)
        db.commit()
        db.refresh(fund)
        logger.info(f"✅ Fund deployment completed - Address: {fund_address}")
        return fund
    
    def get_balances(self, db: Session, fund_id: int) -> Optional[FundBalances]:
        fund = self.get(db, fund_id)
        if not fund:
            return None
        
        return FundBalances(
            total_balance=fund.total_balance,
            available_balance=fund.available_balance,
            total_invested=fund.total_invested,
            total_gross_deposited=fund.total_gross_deposited,
            total_fees_paid=fund.total_fees_paid,
            total_withdrawn=fund.total_withdrawn
        )
    
    def get_stats(self, db: Session, fund_id: int) -> Optional[FundStats]:
        fund = self.get(db, fund_id)
        if not fund:
            return None
        total_deposits = fund.monthly_deposit_count + fund.extra_deposit_count
        avg_deposit = (
            fund.total_gross_deposited / total_deposits 
            if total_deposits > 0 else Decimal(0)
        )

        investment_count = db.query(FundInvestment).filter(
            FundInvestment.fund_id == fund_id,
            FundInvestment.is_active == True
        ).count()
        
        return FundStats(
            total_deposits=total_deposits,
            total_withdrawals=fund.withdrawal_count,
            average_deposit=avg_deposit,
            total_fees_paid=fund.total_fees_paid,
            investment_count=investment_count
        )
    
    def record_deposit(
        self,
        db: Session,
        fund_id: int,
        transaction_hash: str
    ) -> Dict[str, Any]:
        fund = self.get(db, fund_id)
        if not fund:
            raise ValueError("Fund not found")
        logger.info(f"📥 Deposit recorded for fund {fund_id}")
        return {"success": True, "fund_id": fund_id}
    
    def record_withdrawal(
        self,
        db: Session,
        fund_id: int,
        transaction_hash: str
    ) -> Dict[str, Any]:
        fund = self.get(db, fund_id)
        if not fund:
            raise ValueError("Fund not found")
        
        if not fund.retirement_started:
            raise ValueError("Cannot withdraw before retirement started")
        
        logger.info(f"📤 Withdrawal recorded for fund {fund_id}")
        return {"success": True, "fund_id": fund_id}
    
    def start_retirement(
        self,
        db: Session,
        fund_id: int,
        transaction_hash: str
    ) -> Dict[str, Any]:
        fund = self.get(db, fund_id)
        if not fund:
            raise ValueError("Fund not found")
        
        if fund.retirement_started:
            raise ValueError("Retirement already started")
        
        if not fund.early_retirement_approved:
            if datetime.utcnow() < fund.timelock_end:
                raise ValueError("Timelock period not finished")
        fund.retirement_started = True
        fund.retirement_start_time = datetime.utcnow()
        db.commit()
        db.refresh(fund)
        logger.info(f"🎉 Retirement started for fund {fund_id}")
        return {"success": True, "fund_id": fund_id, "started_at": fund.retirement_start_time}
    
    def can_start_retirement(self, db: Session, fund_id: int) -> Optional[Dict[str, Any]]:
        fund = self.get(db, fund_id)
        if not fund:
            return None
        if fund.retirement_started:
            return {"can_retire": False, "reason": "Already retired"}
        if fund.early_retirement_approved:
            return {"can_retire": True, "reason": "Early retirement approved"}
        if datetime.utcnow() >= fund.timelock_end:
            return {"can_retire": True, "reason": "Timelock period completed"}
        days_remaining = (fund.timelock_end - datetime.utcnow()).days
        return {
            "can_retire": False,
            "reason": f"Timelock period not finished",
            "days_remaining": days_remaining
        }
    
    def configure_auto_withdrawal(
        self,
        db: Session,
        fund_id: int,
        config: AutoWithdrawalConfig
    ) -> Dict[str, Any]:
        fund = self.get(db, fund_id)
        if not fund:
            raise ValueError("Fund not found")
        fund.auto_withdrawal_enabled = config.enabled
        fund.auto_withdrawal_amount = config.amount
        fund.auto_withdrawal_interval = config.interval_days * 86400
        if config.enabled and fund.retirement_started:
            fund.next_auto_withdrawal_time = (
                datetime.utcnow() + timedelta(seconds=fund.auto_withdrawal_interval)
            )
        db.commit()
        db.refresh(fund)
        logger.info(f"⚙️ Auto-withdrawal configured for fund {fund_id}")
        return {"success": True, "config": config}
    
    def get_auto_withdrawal_info(
        self,
        db: Session,
        fund_id: int
    ) -> Optional[AutoWithdrawalInfo]:
        fund = self.get(db, fund_id)
        if not fund:
            return None
        
        return AutoWithdrawalInfo(
            enabled=fund.auto_withdrawal_enabled,
            amount=fund.auto_withdrawal_amount,
            interval=fund.auto_withdrawal_interval,
            next_execution_time=fund.next_auto_withdrawal_time,
            execution_count=fund.auto_withdrawal_execution_count,
            last_execution_time=fund.last_auto_withdrawal_time
        )
    
    def get_all_funds(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        retirement_status: Optional[str] = None
    ) -> List[PersonalFund]:
        query = db.query(PersonalFund)
        
        if retirement_status:
            if retirement_status == "retired":
                query = query.filter(PersonalFund.retirement_started == True)
            elif retirement_status == "ready":
                query = query.filter(
                    PersonalFund.retirement_started == False,
                    PersonalFund.timelock_end <= datetime.utcnow()
                )
            elif retirement_status == "accumulating":
                query = query.filter(
                    PersonalFund.retirement_started == False,
                    PersonalFund.timelock_end > datetime.utcnow()
                )
        return query.order_by(desc(PersonalFund.created_at)).offset(skip).limit(limit).all()
    
    def get_funds_ready_for_retirement(self, db: Session) -> List[PersonalFund]:
        return db.query(PersonalFund).filter(
            PersonalFund.retirement_started == False,
            PersonalFund.initialized == True,
            or_(
                PersonalFund.early_retirement_approved == True,
                PersonalFund.timelock_end <= datetime.utcnow()
            )
        ).all()
    
    def get_funds_in_retirement(self, db: Session) -> List[PersonalFund]:
        return db.query(PersonalFund).filter(
            PersonalFund.retirement_started == True
        ).all()
    
    @staticmethod
    def _calculate_fee(amount: Decimal) -> Decimal:
        return (amount * Decimal('0.03')).quantize(Decimal('0.000001'))
    async def monitor_fund_creation(self, fund_id: int, wallet_address: str):
        logger.info(f"🔍 Monitoring fund creation for {wallet_address}")

fund_service = FundService()