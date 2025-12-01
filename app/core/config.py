from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Retirement Fund API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API para gestión de fondo de retiro en blockchain"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    FRONTEND_URL: str

    # Auth / JWT
    SECRET_KEY: str = "change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: str
    ADMIN_TOKEN: str 

    ARBITRUM_SEPOLIA_RPC: str = "https://sepolia-rollup.arbitrum.io/rpc"
    ARBITRUM_SEPOLIA_CHAIN_ID: int = 421614
    CONTRACT_ADDRESS_ARBITRUM_SEPOLIA: Optional[str] = None

    ARBITRUM_RPC: str = "https://arb1.arbitrum.io/rpc"
    ARBITRUM_CHAIN_ID: int = 42161
    CONTRACT_ADDRESS_ARBITRUM: Optional[str] = None

    ZKSYNC_RPC: str = "https://mainnet.era.zksync.io"
    ZKSYNC_CHAIN_ID: int = 324
    CONTRACT_ADDRESS_ZKSYNC: Optional[str] = None

    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    LOG_LEVEL: str = "DEBUG"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,  
        extra="allow",
    )

    @property
    def database_url_sync(self) -> str:
        url = self.DATABASE_URL

        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()