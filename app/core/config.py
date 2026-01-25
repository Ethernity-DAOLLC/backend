from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, ConfigDict
from typing import List, Optional, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = Field(
        default="Ethernity DAO",
        description="Project name"
    )
    
    VERSION: str = Field(
        default="1.0.0",
        description="API version"
    )
    
    DESCRIPTION: str = Field(
        default="Decentralized Retirement Fund Platform with Governance",
        description="API description"
    )
    
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    DEBUG: bool = Field(
        default=True,
        description="Debug mode"
    )
    
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API V1 prefix"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ethernity_dao",
        description="PostgreSQL database URL"
    )
    
    DB_POOL_SIZE: int = Field(
        default=20,
        description="Database connection pool size"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=40,
        description="Max database connections overflow"
    )
    
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        description="Connection recycle time in seconds"
    )
    
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="Test connections before using"
    )
    
    DB_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries (for debugging)"
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
        default="change-this-secret-key-in-production-make-it-long-and-random",
        description="Secret key for JWT and encryption"
    )
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7,  # 7 days
        description="Access token expiration time in minutes"
    )
    
    ADMIN_EMAIL: str = Field(
        default="admin@ethernity-dao.com",
        description="Admin email"
    )
    
    ADMIN_PASSWORD: str = Field(
        default="change-this-password",
        description="Admin password"
    )
    
    ADMIN_TOKEN: str = Field(
        default="your-admin-token-change-in-production",
        description="Admin static token for development"
    )

    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    SENDGRID_API_KEY: Optional[str] = Field(
        default=None,
        description="SendGrid API key"
    )
    
    FROM_EMAIL: str = Field(
        default="noreply@ethernity-dao.com",
        description="Default from email"
    )
    
    FROM_NAME: str = Field(
        default="Ethernity DAO",
        description="Default from name"
    )

    SMTP_HOST: Optional[str] = Field(
        default=None,
        description="SMTP host"
    )
    
    SMTP_PORT: int = Field(
        default=587,
        description="SMTP port"
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
        description="Use TLS for SMTP"
    )
    
    @property
    def email_enabled(self) -> bool:
        return bool(self.SENDGRID_API_KEY or (self.SMTP_HOST and self.SMTP_USER))

    SENTRY_DSN: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    LOG_FORMAT: str = Field(
        default="json",
        description="Log format: json or text"
    )

    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Max requests per minute per IP"
    )
    
    BLOCKCHAIN_NETWORK: str = Field(
        default="arbitrum-sepolia",
        description="Blockchain network to use (matches contracts.json keys)"
    )
    
    WEB3_PROVIDER_URL: Optional[str] = Field(
        default=None,
        description="Custom Web3 provider URL (overrides contracts.json RPC)"
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
        description="Blockchain sync interval in seconds"
    )
    
    BLOCKCHAIN_BATCH_SIZE: int = Field(
        default=100,
        description="Number of blocks to process per sync iteration"
    )
    
    BLOCKCHAIN_START_BLOCK: int = Field(
        default=0,
        description="Block number to start syncing from (0 = latest)"
    )

    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL (Redis)"
    )
    
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    
    CELERY_TASK_ALWAYS_EAGER: bool = Field(
        default=False,
        description="Execute tasks synchronously (for testing)"
    )
    
    CELERY_TASK_EAGER_PROPAGATES: bool = Field(
        default=True,
        description="Propagate exceptions in eager mode"
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and sessions"
    )
    
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    
    CACHE_TTL: int = Field(
        default=3600,
        description="Default cache TTL in seconds"
    )

    MAX_UPLOAD_SIZE: int = Field(
        default=10 * 1024 * 1024,  # 10MB
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
        description="Default pagination page size"
    )
    
    MAX_PAGE_SIZE: int = Field(
        default=100,
        description="Maximum pagination page size"
    )

    ENABLE_GOVERNANCE: bool = Field(
        default=True,
        description="Enable governance features"
    )
    
    ENABLE_EARLY_RETIREMENT: bool = Field(
        default=True,
        description="Enable early retirement requests"
    )
    
    ENABLE_AUTO_WITHDRAWAL: bool = Field(
        default=True,
        description="Enable automatic withdrawals"
    )
    
    ENABLE_NOTIFICATIONS: bool = Field(
        default=True,
        description="Enable notification system"
    )
    
    ENABLE_ANALYTICS: bool = Field(
        default=True,
        description="Enable analytics and snapshots"
    )

    TOKEN_BURN_DAY: int = Field(
        default=28,
        description="Day of month for token burns"
    )
    
    TOKEN_RENEW_DAY: int = Field(
        default=1,
        description="Day of month for token renewals"
    )
    
    TOKEN_BURN_WARNING_DAYS: int = Field(
        default=7,
        description="Days before burn to send warnings"
    )

    FUND_FEE_PERCENTAGE: int = Field(
        default=300,  # 3% in basis points
        description="Fund fee percentage in basis points"
    )
    
    MIN_FUND_PRINCIPAL: int = Field(
        default=0,
        description="Minimum fund principal in USDC (6 decimals)"
    )
    
    MAX_FUND_PRINCIPAL: int = Field(
        default=100_000_000_000,  # 100k USDC
        description="Maximum fund principal in USDC (6 decimals)"
    )
    
    MIN_MONTHLY_DEPOSIT: int = Field(
        default=50_000_000,  # 50 USDC
        description="Minimum monthly deposit in USDC (6 decimals)"
    )
    
    MIN_TIMELOCK_YEARS: int = Field(
        default=10,
        description="Minimum timelock period in years"
    )
    
    MAX_TIMELOCK_YEARS: int = Field(
        default=50,
        description="Maximum timelock period in years"
    )

    GOVERNANCE_QUORUM_PERCENTAGE: int = Field(
        default=2000,  # 20% in basis points
        description="Governance quorum percentage"
    )
    
    GOVERNANCE_VOTING_PERIOD: int = Field(
        default=259200,  # 3 days in seconds
        description="Governance voting period in seconds"
    )
    
    GOVERNANCE_EXECUTION_DELAY: int = Field(
        default=172800,  # 2 days in seconds
        description="Governance execution delay in seconds"
    )

    TESTING: bool = Field(
        default=False,
        description="Testing mode"
    )
    
    MOCK_BLOCKCHAIN: bool = Field(
        default=False,
        description="Use mock blockchain for testing"
    )
    
    SKIP_MIGRATIONS: bool = Field(
        default=False,
        description="Skip database migrations on startup"
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
    def database_name(self) -> str:
        try:
            return self.DATABASE_URL.split("/")[-1].split("?")[0]
        except:
            return "unknown"
    
    @property
    def is_local_development(self) -> bool:
        return "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL

    def log_config(self) -> None:
        logger.info("=" * 80)
        logger.info(f"🚀 {self.PROJECT_NAME} v{self.VERSION}")
        logger.info("=" * 80)
        logger.info(f"Environment: {self.ENVIRONMENT}")
        logger.info(f"Debug Mode: {self.DEBUG}")
        logger.info(f"Database: {self.database_name}")
        logger.info(f"Database Pool: {self.DB_POOL_SIZE} + {self.DB_MAX_OVERFLOW}")
        logger.info(f"API Prefix: {self.API_V1_STR}")
        logger.info(f"CORS Origins: {len(self.BACKEND_CORS_ORIGINS)} configured")
        logger.info(f"Email: {'✅ Enabled' if self.email_enabled else '❌ Disabled'}")
        logger.info(f"Rate Limiting: {'✅ Enabled' if self.RATE_LIMIT_ENABLED else '❌ Disabled'}")
        logger.info(f"Sentry: {'✅ Enabled' if self.SENTRY_DSN else '❌ Disabled'}")
        logger.info("-" * 80)
        logger.info("🔗 BLOCKCHAIN CONFIGURATION")
        logger.info(f"Network: {self.BLOCKCHAIN_NETWORK}")
        logger.info(f"Sync Enabled: {'✅' if self.BLOCKCHAIN_SYNC_ENABLED else '❌'}")
        logger.info(f"Sync Interval: {self.BLOCKCHAIN_SYNC_INTERVAL}s")
        logger.info(f"Batch Size: {self.BLOCKCHAIN_BATCH_SIZE} blocks")
        logger.info("-" * 80)
        logger.info("⚙️ CELERY CONFIGURATION")
        logger.info(f"Broker: {self.CELERY_BROKER_URL}")
        logger.info(f"Backend: {self.CELERY_RESULT_BACKEND}")
        logger.info(f"Eager Mode: {'✅' if self.CELERY_TASK_ALWAYS_EAGER else '❌'}")
        logger.info("-" * 80)
        logger.info("🎛️ FEATURE FLAGS")
        logger.info(f"Governance: {'✅' if self.ENABLE_GOVERNANCE else '❌'}")
        logger.info(f"Early Retirement: {'✅' if self.ENABLE_EARLY_RETIREMENT else '❌'}")
        logger.info(f"Auto Withdrawal: {'✅' if self.ENABLE_AUTO_WITHDRAWAL else '❌'}")
        logger.info(f"Notifications: {'✅' if self.ENABLE_NOTIFICATIONS else '❌'}")
        logger.info(f"Analytics: {'✅' if self.ENABLE_ANALYTICS else '❌'}")
        logger.info("=" * 80)
    
    def validate_config(self) -> List[str]:
        warnings = []
        if self.is_production:
            if self.DEBUG:
                warnings.append("⚠️ DEBUG mode is enabled in production")
            if self.SECRET_KEY == "change-this-secret-key-in-production-make-it-long-and-random":
                warnings.append("⚠️ Using default SECRET_KEY in production")
            if self.ADMIN_PASSWORD == "change-this-password":
                warnings.append("⚠️ Using default ADMIN_PASSWORD in production")
            if not self.SENTRY_DSN:
                warnings.append("⚠️ Sentry is not configured in production")
            if self.is_local_development:
                warnings.append("⚠️ Using local database in production environment")
        if not self.email_enabled:
            warnings.append("ℹ️ Email is not configured")
        if self.BLOCKCHAIN_SYNC_ENABLED and not self.WEB3_PROVIDER_URL:
            warnings.append("ℹ️ Using contracts.json RPC (no custom Web3 provider)")
        if self.DB_POOL_SIZE < 5:
            warnings.append("⚠️ Database pool size is very small")
        return warnings
    
    def get_contract_address(self, contract_name: str) -> Optional[str]:
        env_mapping = {
            "token": self.TOKEN_ADDRESS,
            "factory": self.FACTORY_ADDRESS,
            "governance": self.GOVERNANCE_ADDRESS,
            "treasury": self.TREASURY_ADDRESS,
            "protocolRegistry": self.PROTOCOL_REGISTRY_ADDRESS,
            "userPreferences": self.USER_PREFERENCES_ADDRESS,
            "dateTime": self.DATETIME_LIBRARY_ADDRESS,
        }
        return env_mapping.get(contract_name)

settings = Settings()
if not settings.TESTING:
    warnings = settings.validate_config()
    if warnings:
        logger.warning("Configuration warnings detected:")
        for warning in warnings:
            logger.warning(f"  {warning}")

def get_settings() -> Settings:
    return settings

def reload_settings() -> Settings:
    global settings
    settings = Settings()
    return settings
