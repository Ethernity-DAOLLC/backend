from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

class NotificationService(BaseService[Notification]):
    def __init__(self):
        super().__init__(Notification)
    
    def create_notification(
        self,
        db: Session,
        notification: NotificationCreate
    ) -> Notification:
        notif = Notification(**notification.model_dump())
        db.add(notif)
        db.commit()
        db.refresh(notif)
        logger.info(f"🔔 Notification created for user {notification.user_id}")
        return notif
    
    def get_user_notifications(
        self,
        db: Session,
        wallet_address: str,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return []
        
        query = db.query(Notification).filter(Notification.user_id == user.id)
        if unread_only:
            query = query.filter(Notification.read == False)
        return query.order_by(
            desc(Notification.created_at)
        ).offset(skip).limit(limit).all()
    
    def get_unread_count(self, db: Session, wallet_address: str) -> int:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return 0
        
        return db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.read == False
        ).count()
    
    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
        read: bool = True
    ) -> Optional[Notification]:
        notification = self.get(db, notification_id)
        if not notification:
            return None
        
        notification.read = read
        notification.read_at = datetime.utcnow() if read else None
        db.commit()
        db.refresh(notification)
        return notification
    
    def mark_all_read(self, db: Session, wallet_address: str) -> int:
        user = db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            return 0
        
        count = db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.read == False
        ).update({"read": True, "read_at": datetime.utcnow()})
        db.commit()
        
        logger.info(f"✅ Marked {count} notifications as read for {wallet_address}")
        return count
    
    def delete_notification(self, db: Session, notification_id: int) -> bool:
        return self.delete(db, notification_id)

notification_service = NotificationService()