from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from datetime import datetime
import logging

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

class UserService:
    
    @staticmethod
    def get_by_wallet(db: Session, wallet_address: str) -> Optional[User]:
        return db.query(User).filter(
            User.wallet_address == wallet_address.lower()
        ).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower()).first()
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:

        wallet_address = user_data.wallet_address.lower()
        existing = UserService.get_by_wallet(db, wallet_address)
        if existing:
            raise ValueError(f"Wallet {wallet_address} ya está registrada")

        if user_data.email:
            existing_email = UserService.get_by_email(db, user_data.email)
            if existing_email:
                raise ValueError(f"Email {user_data.email} ya está registrado")
        
        db_user = User(
            wallet_address=wallet_address,
            email=user_data.email.lower() if user_data.email else None,
            username=user_data.username,
            full_name=user_data.full_name,
            accepts_marketing=user_data.accepts_marketing,
            accepts_notifications=user_data.accepts_notifications,
            preferred_language=user_data.preferred_language,
            ip_address=user_data.ip_address,
            user_agent=user_data.user_agent,
            last_login=datetime.utcnow()
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"✅ Usuario creado: {wallet_address}")
        return db_user
    
    @staticmethod
    def associate_email(
        db: Session,
        wallet_address: str,
        email: str,
        accepts_marketing: bool = False,
        accepts_notifications: bool = True
    ) -> User:
        wallet_address = wallet_address.lower()
        email = email.lower()

        user = UserService.get_by_wallet(db, wallet_address)
        existing_email = UserService.get_by_email(db, email)
        if existing_email and existing_email.wallet_address != wallet_address:
            raise ValueError(f"Email {email} ya está asociado a otra wallet")
        
        if user:
            user.email = email
            user.accepts_marketing = accepts_marketing
            user.accepts_notifications = accepts_notifications
            user.updated_at = datetime.utcnow()
            logger.info(f"✅ Email actualizado para wallet: {wallet_address}")
        else:
            user = User(
                wallet_address=wallet_address,
                email=email,
                accepts_marketing=accepts_marketing,
                accepts_notifications=accepts_notifications,
                last_login=datetime.utcnow()
            )
            db.add(user)
            logger.info(f"✅ Nuevo usuario creado con email: {wallet_address}")
        
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        user_update: UserUpdate
    ) -> Optional[User]:
        user = UserService.get_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update_last_login(db: Session, wallet_address: str) -> Optional[User]:
        user = UserService.get_by_wallet(db, wallet_address)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_users_for_mailing(
        db: Session,
        accepts_marketing: bool = True,
        is_active: bool = True,
        email_verified: bool = False
    ) -> List[User]:
        query = db.query(User).filter(
            User.email.isnot(None),
            User.is_active == is_active,
            User.is_banned == False
        )
        
        if accepts_marketing:
            query = query.filter(User.accepts_marketing == True)
        
        if email_verified:
            query = query.filter(User.email_verified == True)
        
        return query.all()
    
    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def search_users(
        db: Session,
        search_term: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        search = f"%{search_term.lower()}%"
        return db.query(User).filter(
            or_(
                User.wallet_address.ilike(search),
                User.email.ilike(search),
                User.username.ilike(search)
            )
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def mark_email_sent(db: Session, user_id: int) -> Optional[User]:
        user = UserService.get_by_id(db, user_id)
        if user:
            user.last_email_sent = datetime.utcnow()
            db.commit()
            db.refresh(user)
        return user