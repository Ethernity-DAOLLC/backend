from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional, Dict, Any
from decimal import Decimal
import logging

from app.models.protocol import DeFiProtocol, ProtocolAPYHistory
from app.schemas.protocol import (
    DeFiProtocolCreate, DeFiProtocolUpdate,
    ProtocolWithAPY, ProtocolStats
)
from app.services.base_service import BaseService
from app.core.helpers import basis_points_to_percentage

logger = logging.getLogger(__name__)

class ProtocolService(BaseService[DeFiProtocol]):
    def __init__(self):
        super().__init__(DeFiProtocol)
    
    def get_by_address(self, db: Session, protocol_address: str) -> Optional[DeFiProtocol]:
        return db.query(DeFiProtocol).filter(
            DeFiProtocol.protocol_address == protocol_address
        ).first()
    
    def add_protocol(
        self,
        db: Session,
        protocol_data: DeFiProtocolCreate
    ) -> DeFiProtocol:
        existing = self.get_by_address(db, protocol_data.protocol_address)
        if existing:
            raise ValueError("Protocol already exists")
        
        protocol = DeFiProtocol(
            protocol_address=protocol_data.protocol_address,
            name=protocol_data.name,
            apy=protocol_data.apy,
            risk_level=protocol_data.risk_level,
            is_active=True,
            verified=False,
            added_timestamp=datetime.utcnow()
        )
        
        db.add(protocol)
        db.commit()
        db.refresh(protocol)
        logger.info(f"➕ Protocol added: {protocol.name}")
        return protocol
    
    def update_protocol(
        self,
        db: Session,
        protocol_id: int,
        update_data: DeFiProtocolUpdate
    ) -> Optional[DeFiProtocol]:
        protocol = self.get(db, protocol_id)
        if not protocol:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(protocol, field, value)
        
        protocol.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(protocol)
        logger.info(f"✏️ Protocol updated: {protocol.name}")
        return protocol
    
    def verify_protocol(self, db: Session, protocol_id: int) -> Optional[DeFiProtocol]:
        protocol = self.get(db, protocol_id)
        if not protocol:
            return None
        
        protocol.verified = True
        protocol.verified_at = datetime.utcnow()
        protocol.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(protocol)
        logger.info(f"✅ Protocol verified: {protocol.name}")
        return protocol
    
    def toggle_status(self, db: Session, protocol_id: int) -> Optional[DeFiProtocol]:
        protocol = self.get(db, protocol_id)
        if not protocol:
            return None
        
        protocol.is_active = not protocol.is_active
        protocol.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(protocol)
        logger.info(f"🔄 Protocol {'activated' if protocol.is_active else 'deactivated'}: {protocol.name}")
        return protocol
    
    def get_protocols(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        verified_only: bool = False,
        risk_level: Optional[int] = None
    ) -> List[DeFiProtocol]:
        query = db.query(DeFiProtocol)
        if active_only:
            query = query.filter(DeFiProtocol.is_active == True)
        if verified_only:
            query = query.filter(DeFiProtocol.verified == True)
        if risk_level is not None:
            query = query.filter(DeFiProtocol.risk_level == risk_level)
        return query.order_by(desc(DeFiProtocol.apy)).offset(skip).limit(limit).all()
    
    def get_best_apy(
        self,
        db: Session,
        risk_level: Optional[int] = None,
        limit: int = 10
    ) -> List[ProtocolWithAPY]:
        query = db.query(DeFiProtocol).filter(
            DeFiProtocol.is_active == True
        )
        
        if risk_level is not None:
            query = query.filter(DeFiProtocol.risk_level == risk_level)
        protocols = query.order_by(desc(DeFiProtocol.apy)).limit(limit).all()
        
        return [
            ProtocolWithAPY(
                protocol_address=p.protocol_address,
                name=p.name,
                apy=p.apy,
                risk_level=p.risk_level,
                apy_percentage=basis_points_to_percentage(p.apy)
            )
            for p in protocols
        ]
    
    def get_by_risk_level(self, db: Session, risk_level: int) -> List[DeFiProtocol]:
        return db.query(DeFiProtocol).filter(
            DeFiProtocol.is_active == True,
            DeFiProtocol.risk_level == risk_level
        ).all()
    
    def update_apy(
        self,
        db: Session,
        protocol_id: int,
        new_apy: int
    ) -> Dict[str, Any]:
        protocol = self.get(db, protocol_id)
        if not protocol:
            raise ValueError("Protocol not found")
        old_apy = protocol.apy
        protocol.apy = new_apy
        protocol.last_updated = datetime.utcnow()
        history = ProtocolAPYHistory(
            protocol_id=protocol_id,
            old_apy=old_apy,
            new_apy=new_apy
        )
        
        db.add(history)
        db.commit()
        logger.info(f"📈 APY updated for {protocol.name}: {old_apy} -> {new_apy}")
        return {"success": True, "old_apy": old_apy, "new_apy": new_apy}
    
    def get_apy_history(
        self,
        db: Session,
        protocol_id: int,
        limit: int = 50
    ) -> List[ProtocolAPYHistory]:
        return db.query(ProtocolAPYHistory).filter(
            ProtocolAPYHistory.protocol_id == protocol_id
        ).order_by(desc(ProtocolAPYHistory.created_at)).limit(limit).all()
    
    def get_stats(self, db: Session) -> ProtocolStats:
        total_protocols = db.query(DeFiProtocol).count()
        active_protocols = db.query(DeFiProtocol).filter(
            DeFiProtocol.is_active == True
        ).count()
        verified_protocols = db.query(DeFiProtocol).filter(
            DeFiProtocol.verified == True
        ).count()
        avg_apy = db.query(func.avg(DeFiProtocol.apy)).filter(
            DeFiProtocol.is_active == True
        ).scalar() or 0
        total_tvl = db.query(func.sum(DeFiProtocol.total_deposited)).scalar() or Decimal(0)
        
        return ProtocolStats(
            total_protocols=total_protocols,
            active_protocols=active_protocols,
            verified_protocols=verified_protocols,
            average_apy=int(avg_apy),
            total_tvl=total_tvl
        )

protocol_service = ProtocolService()