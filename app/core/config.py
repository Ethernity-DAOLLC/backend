from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ConfigDict, ValidationError
from typing import List, Optional, Any, Dict
import logging
import os
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",                                     # Ignore extra env vars
        validate_default=True,                              # Validate default values
    )

    PROJECT_NAME: str = Field(
        default="Ethernity DAO",
        description="Project name displayed in API docs and logs"
    )
    
    VERSION: str = Field(
        default="1.0.0",
        description="API version (semver format)"
    )
    
    DESCRIPTION: str = Field(
        default="Decentralized Retirement Fund Platform with Governance",
        description="API description for OpenAPI documentation"
    )
 
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production, testing"
    )
    
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode (verbose logging, detailed errors)"
    )
    
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API V1 route prefix"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ethernity_dao",
        description="PostgreSQL database URL (supports Supabase)"
    )
    
    DB_POOL_SIZE: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Database connection pool size"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=40,
        ge=0,
        le=100,
        description="Max database connections overflow"
    )
    
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        description="Connection recycle time in seconds (prevent stale connections)"
    )
    
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="Test connections before using (prevents dropped connections)"
    )
    
    DB_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries to console (for debugging)"
    )
    
    @property
    def database_url_sync(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql://")
    
    @property
    def database_url_async(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def is_supabase(self) -> bool:
        return "supabase" in self.DATABASE_URL.lower()

    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production-make-it-long-and-random-minimum-32-characters",
        min_length=32,
        description="Secret key for JWT signing and encryption (CHANGE IN PRODUCTION)"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,                                   # 7 days
        ge=15,
        description="Access token expiration time in minutes"
    )
    
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 30,                                   # 30 days
        ge=60,
        description="Refresh token expiration time in minutes"
    )

    ADMIN_EMAIL: str = Field(
        default="admin@ethernity-dao.com",
        description="Admin email address"
    )
    
    ADMIN_PASSWORD: str = Field(
        default="change-this-password",
        min_length=8,
        description="Admin password (CHANGE IN PRODUCTION)"
    )
    
    ADMIN_TOKEN: str = Field(
        default="your-admin-token-change-in-production",
        description="Admin static token for development"
    )

    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:5174,http://127.0.0.1:3000,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins (frontend URLs)"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> str:
        if isinstance(v, str):
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return ",".join(origins)
        elif isinstance(v, list):
            origins = [str(origin).strip() for origin in v if origin]
            return ",".join(origins)
        raise ValueError(f"CORS origins must be string or list, got: {type(v)}")
    
    @property
    def cors_origins_list(self) -> List[str]:
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def cors_origins_display(self) -> str:
        origins = self.cors_origins_list
        if len(origins) <= 3:
            return ", ".join(origins)
        return f"{', '.join(origins[:3])} ... +{len(origins) - 3} more"
 
    SENDGRID_API_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid API key for transactional emails"
    )
 
    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP server host (e.g., smtp.gmail.com)"
    )
    
    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port (587 for TLS, 465 for SSL)"
    )
    
    SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    
    SMTP_TLS: bool = Field(
        default=True,
        description="Use TLS for SMTP connection"
    )
 
    FROM_EMAIL: str = Field(
        default="noreply@ethernity-dao.com",
        description="Default sender email address"
    )
    
    FROM_NAME: str = Field(
        default="Ethernity DAO",
        description="Default sender name"
    )
    
    @property
    def email_enabled(self) -> bool:
        """Check if email service is properly configured"""
        return bool(
            self.SENDGRID_API_KEY or 
            (self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)
        )
 
    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking and monitoring"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json (production) or text (development)"
    )
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
 
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting middleware"
    )
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        ge=1,
        le=10000,
        description="Max requests per minute per IP address"
    )
    
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Max requests per hour per IP address"
    )
 
    BLOCKCHAIN_NETWORK: str = Field(
        default="arbitrum-sepolia",
        description="Blockchain network identifier (matches contracts.json keys)"
    )
    
    WEB3_PROVIDER_URL: Optional[str] = Field(
        default=None,
        description="Custom Web3 RPC provider URL (overrides contracts.json RPC)"
    )
    
    WEB3_PROVIDER_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Web3 provider request timeout in seconds"
    )
 
    TOKEN_ADDRESS: Optional[str] = Field(
        default=None,
        description="GERAS Token contract address"
    )
    
    FACTORY_ADDRESS: Optional[str] = Field(
        default=None,
        description="PersonalFundFactory contract address"
    )
    
    GOVERNANCE_ADDRESS: Optional[str] = Field(
        default=None,
        description="Governance contract address"
    )
    
    TREASURY_ADDRESS: Optional[str] = Field(
        default=None,
        description="Treasury contract address"
    )
    
    PROTOCOL_REGISTRY_ADDRESS: Optional[str] = Field(
        default=None,
        description="ProtocolRegistry contract address"
    )
    
    USER_PREFERENCES_ADDRESS: Optional[str] = Field(
        default=None,
        description="UserPreferences contract address"
    )
    
    DATETIME_LIBRARY_ADDRESS: Optional[str] = Field(
        default=None,
        description="DateTime library contract address"
    )
 
    BLOCKCHAIN_SYNC_ENABLED: bool = Field(
        default=True,
        description="Enable blockchain event syncing"
    )
    
    BLOCKCHAIN_SYNC_INTERVAL: int = Field(
        default=30,
        ge=5,
        le=3600,
        description="Blockchain sync interval in seconds"
    )
    
    BLOCKCHAIN_SYNC_FROM_BLOCK: Optional[int] = Field(
        default=None,
        description="Start syncing from this block (None = latest)"
    )
    
    BLOCKCHAIN_BATCH_SIZE: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="Batch size for blockchain event queries"
    )
 
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery message broker URL"
    )
    
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    
    CELERY_TASK_ALWAYS_EAGER: bool = Field(
        default=False,
        description="Execute Celery tasks synchronously (for testing)"
    )
    
    CELERY_TASK_EAGER_PROPAGATES: bool = Field(
        default=True,
        description="Propagate exceptions in eager mode"
    )
    
    CELERY_TASK_TIME_LIMIT: int = Field(
        default=300,
        ge=10,
        description="Celery task hard time limit in seconds"
    )
    
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(
        default=240,
        ge=10,
        description="Celery task soft time limit in seconds"
    )
 
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and sessions"
    )
    
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password (if required)"
    )
    
    REDIS_MAX_CONNECTIONS: int = Field(
        default=50,
        ge=10,
        le=1000,
        description="Max Redis connections in pool"
    )
    
    CACHE_TTL: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default cache TTL in seconds (1 hour default)"
    )
    
    CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable Redis caching"
    )
 
    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,                                # 10MB
        ge=1024,
        le=100 * 1024 * 1024,                                    # Max 100MB
        description="Max file upload size in bytes"
    )
    
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".jpg", ".jpeg", ".png", ".csv", ".xlsx"],
        description="Allowed file extensions for upload"
    )
    
    UPLOAD_DIR: Path = Field(
        default=Path("uploads"),
        description="Directory for file uploads"
    )
 
    DEFAULT_PAGE_SIZE: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Default pagination page size"
    )
    
    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum pagination page size"
    )
 
    ENABLE_GOVERNANCE: bool = Field(
        default=True,
        description="Enable governance voting features"
    )
    
    ENABLE_EARLY_RETIREMENT: bool = Field(
        default=True,
        description="Enable early retirement request features"
    )
    
    ENABLE_AUTO_WITHDRAWAL: bool = Field(
        default=True,
        description="Enable automatic monthly withdrawals"
    )
    
    ENABLE_NOTIFICATIONS: bool = Field(
        default=True,
        description="Enable notification system"
    )
    
    ENABLE_ANALYTICS: bool = Field(
        default=True,
        description="Enable analytics and snapshots"
    )
    
    ENABLE_DOCS: bool = Field(
        default=True,
        description="Enable OpenAPI documentation (/docs, /redoc)"
    )
 
    TOKEN_BURN_DAY: int = Field(
        default=28,
        ge=1,
        le=28,
        description="Day of month for token burns"
    )
    
    TOKEN_RENEW_DAY: int = Field(
        default=1,
        ge=1,
        le=28,
        description="Day of month for token renewals"
    )
    
    TOKEN_BURN_WARNING_DAYS: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Days before burn to send warning notifications"
    )
 
    FUND_FEE_PERCENTAGE: int = Field(
        default=300,                                 # 3% in basis points (300/10000 = 0.03)
        ge=0,
        le=1000,                                     # Max 10%
        description="Fund creation fee in basis points (100 = 1%)"
    )
    
    MIN_FUND_PRINCIPAL: int = Field(
        default=0,
        ge=0,
        description="Minimum fund principal in USDC wei (6 decimals)"
    )
    
    MAX_FUND_PRINCIPAL: int = Field(
        default=100_000_000_000,                       # 100k USDC
        ge=0, 
        description="Maximum fund principal in USDC wei (6 decimals)"
    )
    
    MIN_MONTHLY_DEPOSIT: int = Field(
        default=50_000_000,                             # 50 USDC
        ge=0,
        description="Minimum monthly deposit in USDC wei (6 decimals)"
    )
    
    MIN_TIMELOCK_YEARS: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Minimum timelock period in years"
    )
    
    MAX_TIMELOCK_YEARS: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum timelock period in years"
    )

    GOVERNANCE_QUORUM_PERCENTAGE: int = Field(
        default=2000,                             # 20% in basis points
        ge=100,
        le=10000,
        description="Governance quorum percentage in basis points"
    )
    
    GOVERNANCE_VOTING_PERIOD: int = Field(
        default=259200,                           # 3 days in seconds
        ge=3600,                                  # Min 1 hour
        le=2592000,                               # Max 30 days
        description="Governance voting period in seconds"
    )
    
    GOVERNANCE_EXECUTION_DELAY: int = Field(
        default=172800,                           # 2 days in seconds
        ge=0,
        le=604800,                                 # Max 7 days
        description="Governance execution delay in seconds (timelock)"
    )

    TESTING: bool = Field(
        default=False,
        description="Testing mode (disables external services)"
    )
    
    MOCK_BLOCKCHAIN: bool = Field(
        default=False,
        description="Use mock blockchain for testing"
    )
    
    SKIP_MIGRATIONS: bool = Field(
        default=False,
        description="Skip database migrations on startup"
    )
    
    PROFILING_ENABLED: bool = Field(
        default=False,
        description="Enable API profiling middleware"
    )

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() == "testing" or self.TESTING
    
    @property
    def database_name(self) -> str:
        try:
            return self.DATABASE_URL.split("/")[-1].split("?")[0]
        except Exception:
            return "unknown"
    
    @property
    def is_local_development(self) -> bool:
        return "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL
    
    @property
    def should_show_docs(self) -> bool:
        return self.ENABLE_DOCS and not self.is_production

    def log_config(self) -> None:
        logger.info("=" * 80)
        logger.info(f"🚀 {self.PROJECT_NAME} v{self.VERSION}")
        logger.info("=" * 80)
        logger.info(f"📍 Environment: {self.ENVIRONMENT}")
        logger.info(f"🐛 Debug Mode: {'✅ ON' if self.DEBUG else '❌ OFF'}")
        logger.info(f"💾 Database: {self.database_name} ({'Supabase' if self.is_supabase else 'PostgreSQL'})")
        logger.info(f"🔗 Database Pool: {self.DB_POOL_SIZE} + {self.DB_MAX_OVERFLOW} overflow")
        logger.info(f"📡 API Prefix: {self.API_V1_STR}")
        logger.info(f"📚 API Docs: {'✅ Enabled' if self.should_show_docs else '❌ Disabled'}")
        logger.info("-" * 80)
        logger.info("🌐 CORS CONFIGURATION")
        logger.info(f"   Allowed Origins: {len(self.cors_origins_list)} configured")
        logger.info(f"   Origins: {self.cors_origins_display}")
        logger.info("-" * 80)
        logger.info("📧 EMAIL CONFIGURATION")
        logger.info(f"   Status: {'✅ Enabled' if self.email_enabled else '❌ Disabled'}")
        if self.SENDGRID_API_KEY:
            logger.info(f"   Provider: SendGrid")
        elif self.SMTP_HOST:
            logger.info(f"   Provider: SMTP ({self.SMTP_HOST}:{self.SMTP_PORT})")
        logger.info(f"   From: {self.FROM_NAME} <{self.FROM_EMAIL}>")
        logger.info("-" * 80)
        logger.info("🔐 SECURITY")
        logger.info(f"   Rate Limiting: {'✅ Enabled' if self.RATE_LIMIT_ENABLED else '❌ Disabled'}")
        if self.RATE_LIMIT_ENABLED:
            logger.info(f"   Limits: {self.RATE_LIMIT_PER_MINUTE}/min, {self.RATE_LIMIT_PER_HOUR}/hour")
        logger.info(f"   Sentry: {'✅ Enabled' if self.SENTRY_DSN else '❌ Disabled'}")
        logger.info("-" * 80)
        logger.info("🔗 BLOCKCHAIN CONFIGURATION")
        logger.info(f"   Network: {self.BLOCKCHAIN_NETWORK}")
        logger.info(f"   Sync Enabled: {'✅' if self.BLOCKCHAIN_SYNC_ENABLED else '❌'}")
        if self.BLOCKCHAIN_SYNC_ENABLED:
            logger.info(f"   Sync Interval: {self.BLOCKCHAIN_SYNC_INTERVAL}s")
            logger.info(f"   Batch Size: {self.BLOCKCHAIN_BATCH_SIZE} blocks")
        logger.info("-" * 80)
        logger.info("⚙️ CELERY CONFIGURATION")
        logger.info(f"   Broker: {self.CELERY_BROKER_URL}")
        logger.info(f"   Backend: {self.CELERY_RESULT_BACKEND}")
        logger.info(f"   Eager Mode: {'✅' if self.CELERY_TASK_ALWAYS_EAGER else '❌'}")
        logger.info(f"   Task Time Limit: {self.CELERY_TASK_TIME_LIMIT}s")
        logger.info("-" * 80)
        logger.info("💰 REDIS & CACHE")
        logger.info(f"   Redis: {self.REDIS_URL}")
        logger.info(f"   Cache: {'✅ Enabled' if self.CACHE_ENABLED else '❌ Disabled'}")
        if self.CACHE_ENABLED:
            logger.info(f"   Cache TTL: {self.CACHE_TTL}s ({self.CACHE_TTL // 60} minutes)")
        logger.info("-" * 80)
        logger.info("🎛️ FEATURE FLAGS")
        logger.info(f"   Governance: {'✅' if self.ENABLE_GOVERNANCE else '❌'}")
        logger.info(f"   Early Retirement: {'✅' if self.ENABLE_EARLY_RETIREMENT else '❌'}")
        logger.info(f"   Auto Withdrawal: {'✅' if self.ENABLE_AUTO_WITHDRAWAL else '❌'}")
        logger.info(f"   Notifications: {'✅' if self.ENABLE_NOTIFICATIONS else '❌'}")
        logger.info(f"   Analytics: {'✅' if self.ENABLE_ANALYTICS else '❌'}")
        logger.info("=" * 80)
    
    def validate_config(self) -> List[str]:
        warnings = []
        if self.is_production:
            if self.DEBUG:
                warnings.append("⚠️ DEBUG mode is enabled in production environment")
            
            if "change-this" in self.SECRET_KEY.lower():
                warnings.append("🚨 CRITICAL: Using default SECRET_KEY in production")
            
            if "change-this" in self.ADMIN_PASSWORD.lower():
                warnings.append("🚨 CRITICAL: Using default ADMIN_PASSWORD in production")
            
            if len(self.SECRET_KEY) < 32:
                warnings.append("⚠️ SECRET_KEY is too short (minimum 32 characters recommended)")
            
            if not self.SENTRY_DSN:
                warnings.append("⚠️ Sentry is not configured (error tracking disabled)")
            
            if self.is_local_development:
                warnings.append("⚠️ Using local database in production environment")
            
            if len(self.cors_origins_list) == 0:
                warnings.append("⚠️ No CORS origins configured (frontend may not work)")
            localhost_origins = [o for o in self.cors_origins_list if "localhost" in o or "127.0.0.1" in o]
            if localhost_origins:
                warnings.append(f"⚠️ Localhost origins in production CORS: {', '.join(localhost_origins)}")
        if not self.email_enabled:
            warnings.append("ℹ️ Email service is not configured")
        if self.BLOCKCHAIN_SYNC_ENABLED and not self.WEB3_PROVIDER_URL:
            warnings.append("ℹ️ Using contracts.json RPC (no custom Web3 provider)")
        if self.DB_POOL_SIZE < 5:
            warnings.append("⚠️ Database pool size is very small (may cause performance issues)")
        
        if self.DB_POOL_SIZE > 50 and self.is_local_development:
            warnings.append("ℹ️ Large database pool for local development (may be unnecessary)")
        if not self.RATE_LIMIT_ENABLED and self.is_production:
            warnings.append("⚠️ Rate limiting is disabled in production")
        if len(self.cors_origins_list) > 20:
            warnings.append("ℹ️ Large number of CORS origins (consider using patterns)")
        
        return warnings
    
    def get_contract_address(self, contract_name: str) -> Optional[str]:
        env_mapping = {
            "token": self.TOKEN_ADDRESS,
            "geras": self.TOKEN_ADDRESS,
            "factory": self.FACTORY_ADDRESS,
            "personalFundFactory": self.FACTORY_ADDRESS,
            "governance": self.GOVERNANCE_ADDRESS,
            "treasury": self.TREASURY_ADDRESS,
            "protocolRegistry": self.PROTOCOL_REGISTRY_ADDRESS,
            "protocol_registry": self.PROTOCOL_REGISTRY_ADDRESS,
            "userPreferences": self.USER_PREFERENCES_ADDRESS,
            "user_preferences": self.USER_PREFERENCES_ADDRESS,
            "dateTime": self.DATETIME_LIBRARY_ADDRESS,
            "datetime": self.DATETIME_LIBRARY_ADDRESS,
        }
        return env_mapping.get(contract_name)
    
    def to_dict(self) -> Dict[str, Any]:
        sensitive_fields = {
            "SECRET_KEY", "ADMIN_PASSWORD", "ADMIN_TOKEN",
            "DATABASE_URL", "SENDGRID_API_KEY", "SMTP_PASSWORD",
            "REDIS_PASSWORD", "SENTRY_DSN"
        }
        
        return {
            k: ("***REDACTED***" if k in sensitive_fields else v)
            for k, v in self.model_dump().items()
        }

@lru_cache()
def get_settings() -> Settings:
    return Settings()
settings = get_settings()

if not settings.TESTING:
    warnings = settings.validate_config()
    if warnings:
        logger.warning("⚠️ Configuration warnings detected:")
        for warning in warnings:
            logger.warning(f"   {warning}")

def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def validate_settings() -> bool:
    try:
        settings = get_settings()
        warnings = settings.validate_config()
        critical_warnings = [w for w in warnings if "CRITICAL" in w]
        if critical_warnings:
            for warning in critical_warnings:
                logger.error(warning)
            return False
        
        return True
    except ValidationError as e:
        logger.error(f"Settings validation failed: {e}")
        return False
