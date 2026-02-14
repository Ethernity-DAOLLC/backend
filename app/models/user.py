from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(100), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    accepts_marketing = Column(Boolean, default=False)
    accepts_notifications = Column(Boolean, default=True)
    preferred_language = Column(String(5), default="en")

    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_email_sent = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    token_holder = relationship(
        "TokenHolder", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    personal_fund = relationship(
        "PersonalFund",
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan"
    )

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    proposals = relationship(
        "Proposal",
        back_populates="proposer",
        cascade="all, delete-orphan"
    )
    
    votes = relationship(
        "Vote",
        back_populates="voter",
        cascade="all, delete-orphan"
    )

    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    voter_stats = relationship(
        "VoterStats",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.wallet_address} - {self.email}>"

    @property
    def has_token(self) -> bool:
        return self.token_holder is not None and self.token_holder.is_active
    
    @property
    def has_fund(self) -> bool:
        return self.personal_fund is not None
    
    @property
    def can_vote(self) -> bool:
        return self.has_token and self.token_holder.balance > 0
    
    @property
    def is_in_retirement(self) -> bool:
        return (
            self.has_fund and 
            self.personal_fund.retirement_started
        )
    
    def get_fund_status(self) -> str:
        if not self.has_fund:
            return "NO_FUND"
        fund = self.personal_fund
        if fund.retirement_started:
            return "RETIRED"
        elif fund.early_retirement_approved:
            return "EARLY_APPROVED"
        elif datetime.utcnow() >= fund.timelock_end:
            return "READY_FOR_RETIREMENT"
        else:
            return "ACCUMULATING"