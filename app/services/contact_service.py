from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.models.contact import Contact
from app.schemas.contact import ContactCreate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ContactService(BaseService[Contact]):
    def __init__(self):
        super().__init__(Contact)

    def create_contact(
        self,
        db: Session,
        contact_in: ContactCreate,
        client_info: dict | None = None
    ) -> Contact:
        # ✅ SOLO datos del dominio
        contact_data = contact_in.model_dump()

        contact = Contact(**contact_data)
        db.add(contact)
        db.commit()
        db.refresh(contact)

        # 🟡 Metadata técnica → logs
        if client_info:
            logger.info(
                "New contact submitted",
                extra={
                    "contact_id": contact.id,
                    "ip": client_info.get("ip_address"),
                    "forwarded_for": client_info.get("forwarded_for"),
                    "user_agent": client_info.get("user_agent"),
                },
            )

        return contact

    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Contact]:
        query = db.query(Contact)
        if unread_only:
            query = query.filter(Contact.is_read.is_(False))
        return query.order_by(desc(Contact.timestamp)).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, contact_id: int) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()

    def mark_as_read(
        self,
        db: Session,
        contact_id: int,
        is_read: bool = True
    ) -> Optional[Contact]:
        contact = self.get_by_id(db, contact_id)

        if not contact:
            return None

        contact.is_read = is_read
        contact.read_at = datetime.utcnow() if is_read else None

        db.commit()
        db.refresh(contact)

        return contact

    def delete_contact(self, db: Session, contact_id: int) -> bool:
        contact = self.get_by_id(db, contact_id)
        if not contact:
            return False

        db.delete(contact)
        db.commit()
        return True

    def get_unread_count(self, db: Session) -> int:
        return db.query(Contact).filter(Contact.is_read.is_(False)).count()

    def get_recent(self, db: Session, days: int = 7) -> List[Contact]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(Contact)
            .filter(Contact.timestamp >= cutoff)
            .order_by(desc(Contact.timestamp))
            .all()
        )

    def get_stats(self, db: Session) -> dict:
        total = db.query(Contact).count()
        unread = self.get_unread_count(db)
        recent = len(self.get_recent(db, days=7))

        return {
            "total_messages": total,
            "unread_messages": unread,
            "messages_last_7_days": recent,
            "read_percentage": round((total - unread) / total * 100, 2) if total > 0 else 0
        }


contact_service = ContactService()
