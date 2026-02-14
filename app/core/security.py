from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib

from app.core.config import Settings, settings
security_scheme = HTTPBearer()

class SecurityManager:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def verify_admin_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ) -> Dict[str, Any]:
        token = credentials.credentials
        if not secrets.compare_digest(token, self.settings.ADMIN_TOKEN):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "role": "admin",
            "authenticated": True,
            "timestamp": datetime.utcnow()
        }
    
    @staticmethod
    def hash_ip(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)

security_manager = SecurityManager(settings)
