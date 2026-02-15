from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter as FastAPIRateLimiter
from redis.asyncio import Redis
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisRateLimiter:
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.enabled = settings.RATE_LIMIT_ENABLED
    
    async def initialize(self):
        if not self.enabled:
            logger.info("⚠️ Rate limiting disabled")
            return
        
        try:
            redis_url = settings.REDIS_URL
            self.redis_client = Redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await FastAPILimiter.init(self.redis_client)
            logger.info("✅ Redis rate limiter initialized")
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis rate limiter: {e}")
            self.enabled = False
    
    async def close(self):
        if self.redis_client:
            await FastAPILimiter.close()
            await self.redis_client.close()
            logger.info("🔌 Redis rate limiter closed")
    
    def get_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"

rate_limiter = RedisRateLimiter()

def rate_limit_default():
    return FastAPIRateLimiter(
        times=settings.RATE_LIMIT_PER_MINUTE,
        seconds=60
    )

def rate_limit_strict():
    return FastAPIRateLimiter(
        times=10,
        seconds=60
    )

def rate_limit_relaxed():
    return FastAPIRateLimiter(
        times=120,
        seconds=60
    )

def rate_limit_hourly():
    """Rate limit por hora"""
    return FastAPIRateLimiter(
        times=settings.RATE_LIMIT_PER_HOUR,
        seconds=3600
    )