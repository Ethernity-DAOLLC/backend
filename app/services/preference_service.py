from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.models.preferences import UserPreference
from app.models.protocol import DeFiProtocol
from app.models.user import User
from app.schemas.preferences import (
    UserPreferenceCreate, UserPreferenceUpdate,
    StrategyRecommendation
)
from app.services.base_service import BaseService
from app.core.enums import RoutingStrategy

logger = logging.getLogger(__name__)

class PreferenceService(BaseService[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)
    
    def get_preferences(self, db: Session, wallet_address: str) -> Optional[UserPreference]:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return None
        
        return db.query(UserPreference).filter(
            UserPreference.user_id == user.id
        ).first()
    
    def create_preferences(
        self,
        db: Session,
        wallet_address: str,
        preferences: UserPreferenceCreate
    ) -> UserPreference:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            raise ValueError("User not found")
        
        existing = self.get_preferences(db, wallet_address)
        if existing:
            raise ValueError("Preferences already exist")
        
        prefs = UserPreference(
            user_id=user.id,
            wallet_address=wallet_address,
            **preferences.model_dump()
        )
        
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        logger.info(f"⚙️ Preferences created for {wallet_address}")
        return prefs
    
    def update_preferences(
        self,
        db: Session,
        wallet_address: str,
        updates: UserPreferenceUpdate
    ) -> Optional[UserPreference]:
        prefs = self.get_preferences(db, wallet_address)
        if not prefs:
            return None
        
        update_dict = updates.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(prefs, field, value)
        prefs.last_update = datetime.utcnow()
        db.commit()
        db.refresh(prefs)
        logger.info(f"✏️ Preferences updated for {wallet_address}")
        return prefs
    
    def get_recommendation(
        self,
        db: Session,
        wallet_address: str
    ) -> Optional[StrategyRecommendation]:
        prefs = self.get_preferences(db, wallet_address)
        if not prefs:
            return None
        
        query = db.query(DeFiProtocol).filter(
            DeFiProtocol.is_active == True,
            DeFiProtocol.risk_level <= prefs.risk_tolerance
        )
        protocol = None
        reason = ""
        
        if prefs.strategy_type == RoutingStrategy.MANUAL:
            if prefs.selected_protocol_id:
                protocol = db.query(DeFiProtocol).filter(
                    DeFiProtocol.id == prefs.selected_protocol_id
                ).first()
                reason = "Manually selected protocol"
        
        elif prefs.strategy_type == RoutingStrategy.BEST_APY:
            protocol = query.order_by(desc(DeFiProtocol.apy)).first()
            reason = "Highest APY within risk tolerance"
        
        elif prefs.strategy_type == RoutingStrategy.RISK_ADJUSTED:
            protocols = query.all()
            best_score = 0
            for p in protocols:
                score = p.apy / p.risk_level
                if score > best_score:
                    best_score = score
                    protocol = p
            reason = "Best risk-adjusted return"
        
        if not protocol:
            return None
        
        return StrategyRecommendation(
            recommended_protocol_id=protocol.id,
            protocol_name=protocol.name,
            protocol_address=protocol.protocol_address,
            apy=protocol.apy,
            risk_level=protocol.risk_level,
            reason=reason
        )

preference_service = PreferenceService()
