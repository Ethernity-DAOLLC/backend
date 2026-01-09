from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from typing import Callable
import time
import logging
import traceback
from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.time()
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.info(
                f"← {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ {request.method} {request.url.path} - Error ({duration:.3f}s): {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration": duration,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                }
            )
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        if settings.is_production:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        identifier = self.rate_limiter.get_identifier(request)
        if not self.rate_limiter.check_rate_limit(
            identifier,
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60
        ):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60
                }
            )
        
        return await call_next(request)