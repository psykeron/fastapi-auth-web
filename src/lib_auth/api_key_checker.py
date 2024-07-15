from typing import List

from pydantic import BaseModel


class InvalidAPIKeyError(Exception):
    pass


class APIEndpoint(BaseModel):
    app: str
    method: str
    endpoint: str


class APIKey(BaseModel):
    key: str
    allowed_endpoints: List[APIEndpoint]


class APIKeyConfig(BaseModel):
    api_keys: List[APIKey]


class APIKeyChecker:
    config: APIKeyConfig

    def __init__(self, config: APIKeyConfig):
        self.config = config

    def check(self, api_key: str, endpoint: APIEndpoint):
        found_api_key = None
        for key in self.config.api_keys:
            if key.key == api_key:
                found_api_key = key
                break

        if found_api_key is None:
            raise InvalidAPIKeyError("Invalid API key")

        for endpoint in found_api_key.allowed_endpoints:
            if (
                (endpoint.app == "*" or endpoint.app == endpoint.app)
                and (endpoint.method == "*" or endpoint.method == endpoint.method)
                and (endpoint.endpoint == "*" or endpoint.endpoint == endpoint.endpoint)
            ):
                return

        raise InvalidAPIKeyError("Invalid API key")
