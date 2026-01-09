from sqlalchemy.orm import Session
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Generator, Optional, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.core.database import db_manager
from app.core.security import security_manager, security_scheme

logger = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    db = db_manager.get_session()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    return security_manager.verify_admin_token(credentials)

class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, list[datetime]] = defaultdict(list)
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 60,
        window_seconds: int = 60
    ) -> bool:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff
        ]
        if len(self.requests[identifier]) >= max_requests:
            return False
        self.requests[identifier].append(now)
        return True
    
    def get_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

rate_limiter = RateLimiter()

def check_rate_limit(request: Request) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    identifier = rate_limiter.get_identifier(request)
    
    if not rate_limiter.check_rate_limit(
        identifier,
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "forwarded_for": request.headers.get("x-forwarded-for"),
    }