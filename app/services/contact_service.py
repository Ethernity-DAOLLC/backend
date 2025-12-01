from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.models.contact import Contact
from app.schemas.contact import ContactCreate

logger = logging.getLogger(__name__)

class ContactService:
    
    @staticmethod
    def create_contact(db: Session, contact_data: ContactCreate) -> Contact:
        try:
            db_contact = Contact(
                name=contact_data.name,
                email=contact_data.email,
                subject=contact_data.subject,
                message=contact_data.message,
                ip_address=contact_data.ip_address,
                user_agent=contact_data.user_agent,
                timestamp=datetime.utcnow(),
                is_read=False
            )
            db.add(db_contact)
            db.commit()
            db.refresh(db_contact)
            
            logger.info(f"Contact message created: {contact_data.email} - {contact_data.subject}")
            
            return db_contact
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating contact: {e}", exc_info=True)
            raise
    
    @staticmethod
    def get_all_contacts(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Contact]:
        query = db.query(Contact)
        
        if unread_only:
            query = query.filter(Contact.is_read == False)
        
        return query.order_by(
            Contact.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_contact_by_id(db: Session, contact_id: int) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id).first()
    
    @staticmethod
    def mark_as_read(db: Session, contact_id: int, is_read: bool = True) -> Optional[Contact]:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        
        if contact:
            contact.is_read = is_read
            db.commit()
            db.refresh(contact)
            logger.info(f"Contact {contact_id} marked as {'read' if is_read else 'unread'}")
        
        return contact
    
    @staticmethod
    def delete_contact(db: Session, contact_id: int) -> bool:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        
        if contact:
            db.delete(contact)
            db.commit()
            logger.info(f"Contact {contact_id} deleted")
            return True
        
        return False
    
    @staticmethod
    def get_unread_count(db: Session) -> int:
        return db.query(Contact).filter(Contact.is_read == False).count()
    
    @staticmethod
    def get_recent_contacts(db: Session, days: int = 7) -> List[Contact]:
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(Contact).filter(
            Contact.timestamp >= since
        ).order_by(Contact.timestamp.desc()).all()