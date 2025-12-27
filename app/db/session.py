from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
database_url = settings.DATABASE_URL

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {}
if "supabase" in database_url.lower() or "pooler.supabase" in database_url.lower():
    connect_args = {"sslmode": "require"}
    logger.info("🔒 SSL mode enabled for Supabase connection")

if connect_args and "sslmode=" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"

logger.info(f"🔗 Connecting to database (SSL: {bool(connect_args)})")

engine = create_engine(
    database_url,
    pool_pre_ping=True,  
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=30,           
    pool_recycle=300,     
    echo=settings.DEBUG,    
    future=True,    
    connect_args=connect_args, 
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

logger.info("✅ Database engine created successfully")