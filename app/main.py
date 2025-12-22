from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import subprocess
import sys
import os
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.debug(f"DB check failed (normal en startup): {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    def run_migrations():
        try:
            logger.info("🔄 Running Alembic migrations...")
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("✅ Migrations OK")
            else:
                logger.warning(f"⚠️ Migration warning: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("❌ Migration timeout - continuing anyway")
        except Exception as e:
            logger.error(f"❌ Migration error: {e}")

    import threading
    migration_thread = threading.Thread(target=run_migrations, daemon=True)
    migration_thread.start()
    logger.info("✅ App ready for healthcheck")
    
    yield

    logger.info("🛑 Shutting down")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "*.railway.app",
        "*.up.railway.app",
        "localhost",
        "127.0.0.1"
    ]
)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"❌ Unhandled: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["root"])
async def root():
    return {
        "status": "ok",
        "message": "Ethernity DAO Backend running",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health", tags=["health"])
async def health():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "initializing",
        "version": settings.VERSION,
        "timestamp": "ok"
    }

@app.get("/api/stats")
async def api_stats():
    return {
        "status": "ok",
        "total_users": 0,
        "total_requests": 0,
        "uptime": "ok"
    }