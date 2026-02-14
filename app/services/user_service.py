from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

class UserService(BaseService[User]):
    def __init__(self):
        super().__init__(User)
    
    def get_by_wallet(self, db: Session, wallet_address: str) -> Optional[User]:
        return db.query(User).filter(User.wallet_address == wallet_address).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def create_user(
        self,
        db: Session,
        user_in: UserCreate,
        client_info: dict = None
    ) -> User:

        existing = self.get_by_wallet(db, user_in.wallet_address)
        if existing:
            raise ValueError(f"User with wallet {user_in.wallet_address} already exists")
        if user_in.email:
            existing_email = self.get_by_email(db, user_in.email)
            if existing_email:
                raise ValueError(f"Email {user_in.email} already registered")
        
        user_data = user_in.model_dump(exclude_unset=True)
        if client_info:
            user_data.update(client_info)
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ User created: {user.wallet_address}")
        return user
    
    def update_user(
        self,
        db: Session,
        user_id: int,
        user_update: UserUpdate
    ) -> Optional[User]:
        user = self.get(db, user_id)
        
        if not user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"✏️ User updated: {user.wallet_address}")
        return user
    
    def associate_email(
        self,
        db: Session,
        wallet_address: str,
        email: str,
        accepts_marketing: bool = False,
        accepts_notifications: bool = True
    ) -> User:
        user = self.get_by_wallet(db, wallet_address)
        email_user = self.get_by_email(db, email)
        if email_user and email_user.wallet_address != wallet_address:
            raise ValueError(f"Email {email} is already registered to another wallet")
        
        if not user:
            user = User(
                wallet_address=wallet_address,
                email=email,
                accepts_marketing=accepts_marketing,
                accepts_notifications=accepts_notifications
            )
            db.add(user)
        else:
            user.email = email
            user.accepts_marketing = accepts_marketing
            user.accepts_notifications = accepts_notifications
        
        db.commit()
        db.refresh(user)
        logger.info(f"📧 Email associated: {wallet_address} -> {email}")
        return user
    
    def update_last_login(
        self,
        db: Session,
        wallet_address: str
    ) -> Optional[User]:
        user = self.get_by_wallet(db, wallet_address)
        
        if not user:
            return None
        
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_all_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        return db.query(User)\
            .order_by(desc(User.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_users_for_mailing(
        self,
        db: Session,
        accepts_marketing: bool = True,
        email_verified: bool = False
    ) -> List[User]:
        query = db.query(User).filter(
            User.email.isnot(None),
            User.is_active == True,
            User.is_banned == False,
            User.accepts_marketing == accepts_marketing
        )
        
        if email_verified:
            query = query.filter(User.email_verified == True)
        
        return query.all()
    
    def search_users(
        self,
        db: Session,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[User]:
        search = f"%{query}%"
        
        return db.query(User).filter(
            or_(
                User.wallet_address.ilike(search),
                User.email.ilike(search),
                User.username.ilike(search),
                User.full_name.ilike(search)
            )
        ).offset(skip).limit(limit).all()
    
    def get_stats(self, db: Session) -> dict:
        total = db.query(User).count()
        with_email = db.query(User).filter(User.email.isnot(None)).count()
        active = db.query(User).filter(User.is_active == True).count()
        marketing = db.query(User).filter(User.accepts_marketing == True).count()
        
        return {
            "total_users": total,
            "users_with_email": with_email,
            "active_users": active,
            "marketing_subscribers": marketing,
        }

user_service = UserService()
