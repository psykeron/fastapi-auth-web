from typing import Optional

from pydantic import BaseModel, SecretStr

from src.lib_auth.api_key_checker import APIKeyConfig
from src.lib_config.config import get_config as lib_config_get_config


class AWSCashmereConfig(BaseModel):
    namespace: str
    region: str
    endpoint: Optional[str] = None
    aws_account_id: str
    aws_secret_access_key: SecretStr
    aws_access_key_id: SecretStr


class AuthenticationConfig(BaseModel):
    public_key: str


class SecurityConfig(BaseModel):
    authentication: AuthenticationConfig
    api_keys: APIKeyConfig


class ServerConfig(BaseModel):
    host: str
    port: int
    reload_on_change: bool = False
    allowed_origins: Optional[list[str]] = None
    log_level: str = "TRACE"


class ObservabilityConfig(BaseModel):
    sentry_dsn: Optional[str] = None


class Config(BaseModel):
    server: ServerConfig
    security: SecurityConfig
    cashmere: AWSCashmereConfig
    observability: ObservabilityConfig


_config: Optional[Config] = None


# load config yaml from oly parameters files found at root of the project in /configuration
def get_config() -> Config:
    global _config

    if _config is not None:
        return _config

    config = lib_config_get_config()
    _config = Config(
        server=ServerConfig(**config["config"]["server"]),
        security=SecurityConfig(
            authentication=AuthenticationConfig(
                public_key=config["config"]["security"]["authentication"]["public_key"]
            ),
            api_keys=APIKeyConfig(api_keys=config["config"]["security"]["api_keys"]),
        ),
        cashmere=AWSCashmereConfig(**config["config"]["cashmere"]),
        observability=ObservabilityConfig(
            sentry_dsn=config["config"].get("observability", {}).get("sentry_dsn", None)
        ),
    )
    return _config
