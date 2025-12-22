from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, check_db_connection  # Usa la función existente
from app.db.base import Base

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")

    if not check_db_connection():
        logger.critical("❌ NO SE PUDO CONECTAR A LA BASE DE DATOS")
        logger.info("💡 Para Railway: Verifica DATABASE_URL en Variables del servicio")
    else:
        logger.info("✅ Base de datos conectada")
    if settings.ENVIRONMENT == "development":
        logger.info("🔄 Creando tablas automáticamente (dev mode)")
        Base.metadata.create_all(bind=engine)
    else:
        logger.info("🔄 PROD: Asumiendo migraciones Alembic aplicadas manualmente")
    
    yield

    logger.info("🛑 Apagando aplicación")

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
        "localhost",
        "127.0.0.1"
    ]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"❌ Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.DEBUG else str(exc)}
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", status_code=200)
async def root():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy - DB failed",
        "message": f"{settings.PROJECT_NAME} v{settings.VERSION}",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_ok else "disconnected",
        "endpoints": f"{settings.API_V1_STR}/health",
        "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else "disabled"
    }

@app.get("/health", status_code=200)
async def health():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
        "uptime": "ok"
    }

@app.get("/ready", status_code=200)
async def ready():
    return {"status": "ready"}