from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

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
    
    # Metadata
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_email_sent = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.wallet_address} - {self.email}>"