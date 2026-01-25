from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import asyncio
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import check_connection, close_db
from app.core.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
)
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    generic_exception_handler,
)
from app.api.deps import rate_limiter
from app.api.v1.api import api_router
from app.blockchain.web3_client import web3_client
from app.blockchain.event_listener import event_listener

setup_logging(settings)
logger = logging.getLogger(__name__)
event_listener_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_listener_task

    logger.info("🚀 Starting Ethernity DAO Backend...")
    settings.log_config()

    if check_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")

    if web3_client.is_connected():
        logger.info(f"✅ Blockchain connected: {web3_client.network_config['name']}")
        logger.info(f"📡 Latest block: {web3_client.get_latest_block()}")
        if settings.ENVIRONMENT != "testing":
            event_listener_task = asyncio.create_task(event_listener.start())
            logger.info("🎧 Blockchain event listener started")
    else:
        logger.warning("⚠️ Blockchain not connected - running in limited mode")

    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=1.0 if settings.is_development else 0.1,
        )
        logger.info("📊 Sentry initialized")
    logger.info("✅ Application startup complete")
    yield

    logger.info("🛑 Shutting down application...")
    if event_listener_task:
        await event_listener.stop()
        event_listener_task.cancel()
        try:
            await event_listener_task
        except asyncio.CancelledError:
            pass
        logger.info("🎧 Event listener stopped")

    close_db()
    logger.info("💾 Database connections closed")
    logger.info("👋 Shutdown complete")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
    max_age=600,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

if settings.is_development or settings.DEBUG:
    app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "blockchain": web3_client.network_config["name"] if web3_client.is_connected() else "disconnected",
        "docs": "/docs" if not settings.is_production else "disabled",
    }

@app.get("/health")
async def health_check():
    db_healthy = check_connection()
    blockchain_connected = web3_client.is_connected()
    
    return {
        "status": "healthy" if (db_healthy and blockchain_connected) else "degraded",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected",
        "blockchain": {
            "connected": blockchain_connected,
            "network": web3_client.network_config["name"] if blockchain_connected else None,
            "latest_block": web3_client.get_latest_block() if blockchain_connected else 0
        },
        "email": "enabled" if settings.email_enabled else "disabled",
    }

app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

if settings.is_development:
    from app.db.session import engine
    
    @app.get("/debug/config")
    async def debug_config():
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database": "connected" if check_connection() else "disconnected",
            "blockchain": web3_client.network_config if web3_client.is_connected() else None,
            "email_enabled": settings.email_enabled,
            "cors_origins": settings.BACKEND_CORS_ORIGINS,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        }
    
    @app.get("/debug/db-pool")
    async def debug_db_pool():
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
        }
    
    @app.get("/debug/blockchain")
    async def debug_blockchain():
        if not web3_client.is_connected():
            return {"error": "Not connected"}
        
        return {
            "connected": True,
            "network": web3_client.network_config["name"],
            "chain_id": web3_client.network_config["chainId"],
            "latest_block": web3_client.get_latest_block(),
            "contracts": web3_client.network_config["contracts"]
        }