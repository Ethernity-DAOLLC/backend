from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import List, Optional, Dict, Any, Union
from functools import lru_cache
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

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

    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://www.ethernity-dao.com",
            "https://ethernity-dao.com",
        ]
    )
    FRONTEND_URL: str = "https://www.ethernity-dao.com"

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: str
    ADMIN_TOKEN: str
    ACTIVE_NETWORK: str = "arbitrum-sepolia"

    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_FROM: Optional[str] = None

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Parse CORS origins from multiple formats:
        - JSON array string: '["http://localhost:3000","https://app.com"]'
        - Comma-separated: 'http://localhost:3000,https://app.com'
        - Single value: 'https://app.com'
        - List (already parsed): ['http://localhost:3000']
        """
        if v is None:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "https://www.ethernity-dao.com",
                "https://ethernity-dao.com",
            ]

        if isinstance(v, list):
            return v

        if isinstance(v, str):
            v = v.strip()

            if not v or v == "*":
                return ["*"]

            if v.startswith('['):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse CORS as JSON: {v}")

            if ',' in v:
                origins = [origin.strip() for origin in v.split(',')]
                return [o for o in origins if o]

            return [v]
        
        # Fallback
        logger.warning(f"Unexpected CORS type: {type(v)}. Using defaults.")
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://www.ethernity-dao.com",
            "https://ethernity-dao.com",
        ]

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

    def get_contracts_config(self) -> Dict[str, Any]:
        contracts_file = Path(__file__).parent.parent / "config" / "contracts.json"
        try:
            with open(contracts_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Contracts file not found: {contracts_file}")
            return {"networks": {}}

    def get_network_config(self, network: Optional[str] = None) -> Dict[str, Any]:
        network_name = network or self.ACTIVE_NETWORK
        contracts_config = self.get_contracts_config()
        return contracts_config.get("networks", {}).get(network_name, {})

    def get_contract_address(self, contract_name: str, network: Optional[str] = None) -> str:
        network_config = self.get_network_config(network)
        return network_config.get("contracts", {}).get(contract_name, "")

    def get_rpc_url(self, network: Optional[str] = None) -> str:
        network_config = self.get_network_config(network)
        return network_config.get("rpc", "")

    def get_chain_id(self, network: Optional[str] = None) -> int:
        network_config = self.get_network_config(network)
        return network_config.get("chainId", 0)

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

Ahora en Railway, configura `BACKEND_CORS_ORIGINS` con cualquiera de estos formatos:

http://localhost:3000,http://localhost:5173,https://www.ethernity-dao.com,https://ethernity-dao.com

https://www.ethernity-dao.com,https://ethernity-dao.com