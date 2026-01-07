from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging

from app.core.config import settings
from app.api.v1.api import api_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.ethernity-dao.com",
        "https://ethernity-dao.com",
        "http://localhost:5173",
        "http://localhost:3000",
        *settings.BACKEND_CORS_ORIGINS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "*.railway.app", 
        "*.up.railway.app", 
        "*.onrender.com",
        "localhost", 
        "127.0.0.1"
    ]
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
logger.info("App initialized - ready for requests")