from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    age = Column(String(10), nullable=False)
    trust_traditional = Column(Integer, nullable=False)  # -2 a 2
    blockchain_familiarity = Column(Integer, nullable=False)
    retirement_concern = Column(Integer, nullable=False)
    has_retirement_plan = Column(Integer, nullable=False)
    values_in_retirement = Column(Integer, nullable=False)
    interested_in_blockchain = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Survey(id={self.id}, age={self.age}, created_at={self.created_at})>"


class SurveyFollowUp(Base):
    __tablename__ = "survey_follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    wants_more_info = Column(Boolean, nullable=False)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SurveyFollowUp(id={self.id}, email={self.email}, wants_more_info={self.wants_more_info})>"