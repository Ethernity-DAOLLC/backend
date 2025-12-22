from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import subprocess
from sqlalchemy import text

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, check_db_connection
from app.db.base import Base

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager - Startup and shutdown events"""
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🔧 Environment: {settings.ENVIRONMENT}")
    if not check_db_connection():
        logger.critical("❌ DATABASE CONNECTION FAILED")
        logger.critical("💡 Railway: Verifica DATABASE_URL en las variables de entorno")
        logger.critical("💡 Formato: postgresql://user:password@host:port/database")
        raise RuntimeError("Cannot start application: Database is unreachable")
    logger.info("✅ Base de datos conectada exitosamente")

    try:
        if settings.ENVIRONMENT == "development":
            logger.info("🔄 DEV MODE: Creando tablas con SQLAlchemy")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tablas creadas/verificadas")
        
        else:
            logger.info("🔄 PRODUCTION MODE: Ejecutando migraciones Alembic")
            try:
                result = subprocess.run(
                    ["alembic", "upgrade", "head"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    logger.info("✅ Migraciones Alembic aplicadas exitosamente")
                    if result.stdout:
                        logger.debug(f"Alembic output: {result.stdout}")
                else:
                    logger.error(f"❌ Alembic falló con código {result.returncode}")
                    logger.error(f"STDERR: {result.stderr}")
                    logger.warning("⚠️ Continuando sin migraciones - puede fallar si hay cambios de schema")
            
            except FileNotFoundError:
                logger.warning("⚠️ Alembic no encontrado - usando SQLAlchemy create_all como fallback")
                Base.metadata.create_all(bind=engine)
            
            except subprocess.TimeoutExpired:
                logger.error("❌ Timeout ejecutando migraciones Alembic")
                raise RuntimeError("Database migration timeout")
    
    except Exception as e:
        logger.critical(f"❌ FALLO EN STARTUP: {e}")
        raise

    logger.info("✅ Aplicación iniciada correctamente")
    logger.info(f"📍 Endpoints disponibles: {settings.API_V1_STR}")
    logger.info(f"📚 Docs: {settings.API_V1_STR}/docs" if settings.DEBUG else "📚 Docs: Deshabilitado en producción")
    yield

    logger.info("🛑 Apagando aplicación gracefully")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "*.railway.app", 
        "localhost",  
        "127.0.0.1",     
        "*"               
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        f"❌ Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )

    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "server_error"
            }
        )

    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
            "path": request.url.path
        }
    )
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", status_code=200, tags=["Health"])
async def root():
    db_ok = check_db_connection()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy: Database connection failed"
        )
    
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "api": {
            "base": settings.API_V1_STR,
            "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else "disabled"
        }
    }


@app.get("/health", status_code=200, tags=["Health"])
async def health():
    """
    Health check endpoint - Verifica estado del servicio
    
    Returns:
        - 200: Servicio saludable
        - 503: Servicio no disponible (DB down)
    """
    db_ok = check_db_connection()
    
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    
    return {
        "status": "healthy",
        "database": "connected",
        "version": settings.VERSION
    }

@app.get("/ready", status_code=200, tags=["Health"])
async def ready():
    db_ok = check_db_connection()
    
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready: Database unreachable"
        )
    
    return {
        "status": "ready",
        "database": "ready"
    }

@app.get("/live", status_code=200, tags=["Health"])
async def liveness():
    return {"status": "alive"}

if settings.DEBUG:
    @app.get("/debug/info", tags=["Debug"])
    async def debug_info():
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "database_url": settings.DATABASE_URL.split("@")[-1] if settings.DATABASE_URL else "Not set",
            "cors_origins": settings.BACKEND_CORS_ORIGINS,
            "log_level": settings.LOG_LEVEL
        }