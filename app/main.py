from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import subprocess
import sys

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base
from sqlalchemy import text

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a base de datos: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🗄️ Database: {settings.DATABASE_URL[:30]}...")

    try:
        logger.info("🔄 Aplicando migraciones de base de datos con Alembic...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("✅ Migraciones aplicadas correctamente")
        else:
            logger.warning(f"⚠️ Alembic devolvió código {result.returncode}: {result.stdout + result.stderr}")
    except Exception as e:
        logger.error(f"❌ Error ejecutando Alembic: {e}")

    if not check_db_connection():
        logger.critical("No se pudo conectar a la base de datos. El servicio continuará, pero puede fallar.")
    
    yield

    logger.info("🛑 Apagando la aplicación")

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
        "ethernity-dao.com",
        "www.ethernity-dao.com",
        "localhost",
        "127.0.0.1"
    ]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    detail = str(exc) if settings.DEBUG else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={
            "detail": detail,
            "type": "internal_error"
        }
    )
app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "disabled in production"
    }

@app.get("/health")
async def health_check():
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "project": settings.PROJECT_NAME
    }

@app.get("/api/stats")
async def get_stats():
    return {
        "total_users": 0,
        "total_contributions": 0,
        "total_withdrawals": 0
    }