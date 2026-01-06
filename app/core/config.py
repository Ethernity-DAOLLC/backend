from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import List, Optional, Dict, Any, Union
from functools import lru_cache
from pathlib import Path
import json
import logging
import os

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

    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_ANON_KEY: Optional[str] = None

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
    ADMIN_PASSWORD: str
    ADMIN_TOKEN: str
    ACTIVE_NETWORK: str = "arbitrum-sepolia"
    EMAIL_FROM: str = "noreply@ethernity-dao.com"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SENDGRID_API_KEY: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_EMAILS: List[str] = Field(default_factory=lambda: ["admin@ethernity-dao.com"])
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
        logger.warning(f"Unexpected CORS type: {type(v)}. Using defaults.")
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://www.ethernity-dao.com",
            "https://ethernity-dao.com",
        ]

    @field_validator('ADMIN_EMAILS', mode='before')
    @classmethod
    def parse_admin_emails(cls, v):
        if v is None:
            return ["admin@ethernity-dao.com"]
        
        if isinstance(v, list):
            return v
        
        if isinstance(v, str):
            if ',' in v:
                return [email.strip() for email in v.split(',') if email.strip()]
            return [v.strip()] if v.strip() else ["admin@ethernity-dao.com"]
        return ["admin@ethernity-dao.com"]

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

    @property
    def email_enabled(self) -> bool:
        has_smtp = bool(self.SMTP_HOST and self.SMTP_USER)
        has_sendgrid = bool(self.SENDGRID_API_KEY)
        return has_smtp or has_sendgrid

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