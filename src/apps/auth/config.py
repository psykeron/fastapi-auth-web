from typing import List, Optional

from pydantic import BaseModel

from src.lib_config.config import get_config as lib_config_get_config


class DatabaseConfig(BaseModel):
    url: str


class PrivateKeyConfig(BaseModel):
    key: str
    password: str


class PublicKeyConfig(BaseModel):
    key: str


class AuthDomainConfig(BaseModel):
    origin: str
    cookie_domain: str
    cookie_is_secure: bool


class Config(BaseModel):
    database: DatabaseConfig
    private_key: Optional[PrivateKeyConfig] = None
    public_key: Optional[PublicKeyConfig] = None
    domains: Optional[List[AuthDomainConfig]] = None


_config: Optional[Config] = None


# load config yaml from oly parameters files found at root of the project in /configuration
def get_config() -> Config:
    global _config

    if _config is not None:
        return _config

    config = lib_config_get_config()
    _config = Config(
        database=config["config"]["apps"]["auth"]["database"],
        private_key=config["config"]["apps"]["auth"]["private_key"],
        public_key=config["config"]["apps"]["auth"]["public_key"],
        domains=config["config"]["apps"]["auth"]["domains"],
    )
    return _config
