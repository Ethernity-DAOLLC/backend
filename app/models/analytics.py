from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, DECIMAL, Date, Text,
    Index, CheckConstraint, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import logging

logger = logging.getLogger(__name__)

class DailySnapshot(Base):
    __tablename__ = "daily_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, unique=True, nullable=False, index=True)
    total_token_holders = Column(Integer, default=0, nullable=False)
    active_token_holders = Column(Integer, default=0, nullable=False)
    total_funds = Column(Integer, default=0, nullable=False)
    active_funds = Column(Integer, default=0, nullable=False)
    funds_in_retirement = Column(Integer, default=0, nullable=False)
    total_deposits_today = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_withdrawals_today = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_fees_today = Column(DECIMAL(18, 6), default=0, nullable=False)
    total_tvl = Column(DECIMAL(18, 6), default=0, nullable=False)  
    active_proposals = Column(Integer, default=0, nullable=False)
    votes_cast_today = Column(Integer, default=0, nullable=False)

    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    __table_args__ = (
        Index('idx_daily_snapshots_date', 'snapshot_date', postgresql_using='btree'),
        CheckConstraint('total_token_holders >= 0', name='check_token_holders_positive'),
        CheckConstraint('total_tvl >= 0', name='check_tvl_positive'),
    )
    
    def __repr__(self):
        return (
            f"<DailySnapshot(date={self.snapshot_date}, "
            f"holders={self.total_token_holders}, "
            f"funds={self.total_funds}, "
            f"tvl={self.total_tvl})>"
        )
    
    @property
    def active_holder_percentage(self) -> float:
        if self.total_token_holders == 0:
            return 0.0
        return (self.active_token_holders / self.total_token_holders) * 100
    
    @property
    def retirement_percentage(self) -> float:
        if self.total_funds == 0:
            return 0.0
        return (self.funds_in_retirement / self.total_funds) * 100
    
    @property
    def net_flow_today(self) -> float:
        return float(self.total_deposits_today - self.total_withdrawals_today)

class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True) 
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    avg_daily_active_holders = Column(Integer, default=0)
    avg_daily_tvl = Column(DECIMAL(18, 6), default=0)
    total_deposits_week = Column(DECIMAL(18, 6), default=0)
    total_withdrawals_week = Column(DECIMAL(18, 6), default=0)
    total_fees_week = Column(DECIMAL(18, 6), default=0)
    new_funds_created = Column(Integer, default=0)
    funds_started_retirement = Column(Integer, default=0)
    proposals_created = Column(Integer, default=0)
    total_votes_cast = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint('year', 'week_number', name='uq_year_week'),
        Index('idx_weekly_reports_date', 'year', 'week_number'),
    )
    
    def __repr__(self):
        return (
            f"<WeeklyReport(year={self.year}, "
            f"week={self.week_number}, "
            f"avg_tvl={self.avg_daily_tvl})>"
        )

class MonthlyReport(Base):
    __tablename__ = "monthly_reports"
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True) 
    total_users_end_of_month = Column(Integer, default=0)
    new_users_this_month = Column(Integer, default=0)
    total_funds_end_of_month = Column(Integer, default=0)
    new_funds_this_month = Column(Integer, default=0)
    funds_in_retirement = Column(Integer, default=0)
    total_deposits_month = Column(DECIMAL(18, 6), default=0)
    total_withdrawals_month = Column(DECIMAL(18, 6), default=0)
    total_fees_collected = Column(DECIMAL(18, 6), default=0)
    avg_tvl_month = Column(DECIMAL(18, 6), default=0)
    ending_tvl = Column(DECIMAL(18, 6), default=0)
    tokens_burned = Column(Integer, default=0)
    tokens_renewed = Column(Integer, default=0)
    proposals_created = Column(Integer, default=0)
    proposals_executed = Column(Integer, default=0)
    total_votes_cast = Column(Integer, default=0)
    user_growth_rate = Column(DECIMAL(5, 2), default=0) 
    tvl_growth_rate = Column(DECIMAL(5, 2), default=0) 

    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    __table_args__ = (
        UniqueConstraint('year', 'month', name='uq_year_month'),
        Index('idx_monthly_reports_date', 'year', 'month'),
        CheckConstraint('month BETWEEN 1 AND 12', name='check_valid_month'),
    )
    
    def __repr__(self):
        return (
            f"<MonthlyReport(year={self.year}, "
            f"month={self.month}, "
            f"tvl={self.ending_tvl})>"
        )
    
    @property
    def month_name(self) -> str:
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return months[self.month - 1] if 1 <= self.month <= 12 else "Unknown"

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), unique=True, nullable=False, index=True)
    metric_value = Column(DECIMAL(18, 6), nullable=False)
    metric_type = Column(String(50), nullable=False)  
    description = Column(Text, nullable=True)
    unit = Column(String(20), nullable=True)  

    last_updated = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    
    __table_args__ = (
        Index('idx_system_metrics_name', 'metric_name'),
        Index('idx_system_metrics_updated', 'last_updated'),
    )
    
    def __repr__(self):
        return (
            f"<SystemMetric(name={self.metric_name}, "
            f"value={self.metric_value}, "
            f"type={self.metric_type})>"
        )

class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False, index=True)
    activity_category = Column(String(50), nullable=False) 
    description = Column(Text, nullable=True)
    related_entity_type = Column(String(50), nullable=True) 
    related_entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )

    user = relationship("User")
    __table_args__ = (
        Index('idx_user_activity_user', 'user_id'),
        Index('idx_user_activity_type', 'activity_type'),
        Index('idx_user_activity_date', 'created_at'),
        Index('idx_user_activity_category', 'activity_category'),
    )
    
    def __repr__(self):
        return (
            f"<UserActivityLog(user_id={self.user_id}, "
            f"type={self.activity_type}, "
            f"created_at={self.created_at})>"
        )

SYSTEM_METRICS = {
    'total_tvl': 'Total Value Locked',
    'total_users': 'Total Registered Users',
    'active_funds': 'Active Personal Funds',
    'total_fees_collected': 'Total Fees Collected',
    'avg_fund_balance': 'Average Fund Balance',
    'total_token_holders': 'Total GERAS Token Holders',
    'active_proposals': 'Active Governance Proposals',
    'blockchain_sync_lag': 'Blockchain Sync Lag (blocks)',
    'daily_active_users': 'Daily Active Users',
    'monthly_active_users': 'Monthly Active Users',
}