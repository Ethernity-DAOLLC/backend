from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.session import SessionLocal
from app.core.config import settings

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"role": "admin", "authenticated": True}

from collections import defaultdict
from datetime import datetime, timedelta

rate_limit_storage = defaultdict(list)

def check_rate_limit(
    identifier: str,
    max_requests: int = 10,
    window_minutes: int = 1
) -> bool:

    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=window_minutes)
    
    rate_limit_storage[identifier] = [
        timestamp for timestamp in rate_limit_storage[identifier]
        if timestamp > cutoff
    ]

    if len(rate_limit_storage[identifier]) >= max_requests:
        return False

    rate_limit_storage[identifier].append(now)
    return True