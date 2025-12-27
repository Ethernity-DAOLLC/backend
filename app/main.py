from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import threading
import subprocess
import sys

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from sqlalchemy import text

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION
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
    allowed_hosts=["*.railway.app", "*.up.railway.app", "localhost", "127.0.0.1"]
)

@app.get("/", tags=["root"])
async def root():
    return {"status": "ok", "message": "Backend running", "version": settings.VERSION}

@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy", "version": settings.VERSION}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal error"})

app.include_router(api_router, prefix=settings.API_V1_STR)

def run_migrations():
    logger.info("Starting background migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=90
        )
        if result.returncode == 0:
            logger.info("Migrations completed successfully")
        else:
            logger.warning(f"Non-critical migration warning: {result.stderr}")
    except Exception as e:
        logger.error(f"Migration failed (non-critical): {e}")
threading.Thread(target=run_migrations, daemon=True).start()

logger.info("App initialized - ready for requests")