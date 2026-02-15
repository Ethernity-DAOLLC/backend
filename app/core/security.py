from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional, Dict, Any
import secrets
import hashlib
import logging

from app.core.config import Settings, settings
from app.core.jwt import jwt_manager

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()

class SecurityManager:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def verify_admin_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ) -> Dict[str, Any]:
        token = credentials.credentials
        if self.settings.is_development:
            if secrets.compare_digest(token, self.settings.ADMIN_TOKEN):
                return {
                    "role": "admin",
                    "authenticated": True,
                    "timestamp": datetime.utcnow()
                }
        try:
            payload = jwt_manager.verify_access_token(token)
            if payload.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return payload
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def verify_user_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ) -> Dict[str, Any]:
        token = credentials.credentials
        
        try:
            payload = jwt_manager.verify_access_token(token)
            return payload
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def hash_ip(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)

security_manager = SecurityManager(settings)