from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
    logger.info("DATABASE_URL convertida de postgres:// a postgresql+psycopg://")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,           
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=30,  
    pool_recycle=300,  
    echo=settings.DEBUG,     
    future=True,                           # Usa la API 2.0 de SQLAlchemy (recomendado)
    connect_args={
        "connect_timeout": 10,
        # "keepalives": 1,         
        # "keepalives_idle": 30,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
    class_=scoped_session, 
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine():
    return engine