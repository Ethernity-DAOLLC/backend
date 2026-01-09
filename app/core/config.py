from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, EmailStr
from typing import List, Optional
from functools import lru_cache
import logging
import os

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ethernity DAO API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API para gestión de fondo de retiro en blockchain"

    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_PRE_PING: bool = Field(default=True)
    DB_POOL_RECYCLE: int = Field(default=300, ge=60)
    DB_ECHO: bool = Field(default=False)

    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_SERVICE_KEY: Optional[str] = Field(default=None)
    SUPABASE_ANON_KEY: Optional[str] = Field(default=None)

    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
        ]
    )
    FRONTEND_URL: str = Field(default="http://localhost:5173")
    SECRET_KEY: str = Field(..., min_length=32)
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)

    ADMIN_PASSWORD: str = Field(..., min_length=8)
    ADMIN_TOKEN: str = Field(..., min_length=16)
    ADMIN_EMAIL: EmailStr = Field(default="admin@ethernity-dao.com")
    ADMIN_EMAILS: List[EmailStr] = Field(
        default_factory=lambda: ["admin@ethernity-dao.com"]
    )

    EMAIL_FROM: EmailStr = Field(default="noreply@ethernity-dao.com")
    EMAIL_FROM_NAME: str = Field(default="Ethernity DAO")
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = Field(default=True)
    SMTP_SSL: bool = Field(default=False)
    SENDGRID_API_KEY: Optional[str] = None

    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, ge=1)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    ACTIVE_NETWORK: str = Field(default="arbitrum-sepolia")
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = Field(default=False)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        validate_default=True,
    )

    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v == "*":
                logger.warning("⚠️ CORS set to '*' - not recommended for production")
                return ["*"]
            if ',' in v:
                return [origin.strip() for origin in v.split(',') if origin.strip()]
            return [v.strip()] if v.strip() else []
        return []
    
    @field_validator('ADMIN_EMAILS', mode='before')
    @classmethod
    def parse_admin_emails(cls, v) -> List[str]:
        if isinstance(v, list):
            return v
        
        if isinstance(v, str):
            if ',' in v:
                return [email.strip() for email in v.split(',') if email.strip()]
            return [v.strip()] if v.strip() else []
        return []
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production', 'testing']
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v

    @property
    def database_url_async(self) -> str:
        return self._convert_db_url("postgresql+asyncpg://")
    
    @property
    def database_url_sync(self) -> str:
        return self._convert_db_url("postgresql+psycopg://")
    
    def _convert_db_url(self, prefix: str) -> str:
        url = self.DATABASE_URL

        for old_prefix in ["postgresql://", "postgres://", 
                          "postgresql+psycopg://", "postgresql+asyncpg://"]:
            if url.startswith(old_prefix):
                url = url.replace(old_prefix, "", 1)
                break
        result = f"{prefix}{url}"

        if self.is_supabase and "sslmode=" not in result:
            separator = "&" if "?" in result else "?"
            result = f"{result}{separator}sslmode=require"
        return result
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"
    
    @property
    def is_supabase(self) -> bool:
        return "supabase" in self.DATABASE_URL.lower()
    
    @property
    def email_enabled(self) -> bool:
        has_smtp = bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)
        has_sendgrid = bool(self.SENDGRID_API_KEY)
        return has_smtp or has_sendgrid
    
    @property
    def use_sendgrid(self) -> bool:
        return bool(self.SENDGRID_API_KEY)
    
    def log_config(self) -> None:
        logger.info("=" * 60)
        logger.info(f"🚀 {self.PROJECT_NAME} v{self.VERSION}")
        logger.info(f"📦 Environment: {self.ENVIRONMENT}")
        logger.info(f"🔍 Debug: {self.DEBUG}")
        logger.info(f"🗄️  Database: {'Supabase' if self.is_supabase else 'PostgreSQL'}")
        logger.info(f"📧 Email: {'Enabled' if self.email_enabled else 'Disabled'}")
        logger.info(f"🌐 CORS Origins: {len(self.BACKEND_CORS_ORIGINS)}")
        logger.info(f"⚡ Rate Limiting: {'Enabled' if self.RATE_LIMIT_ENABLED else 'Disabled'}")
        logger.info("=" * 60)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
