from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text
from sqlalchemy.sql import func
from app.db.base_class import Base
import logging

logger = logging.getLogger(__name__)

class FaucetRequest(Base):
    __tablename__ = "faucet_requests"

    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String(42), index=True, nullable=False)
    amount = Column(Numeric(precision=18, scale=6), nullable=False, default=100.000000)

    tx_hash = Column(String(66), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<FaucetRequest {self.wallet_address} - {self.amount} USDC - {self.status}>"