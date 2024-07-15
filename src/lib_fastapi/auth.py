from typing import Annotated, List

from fastapi import Depends, HTTPException
from fastapi.params import Cookie, Header

from src.lib_auth.api_key_checker import APIEndpoint, APIKeyChecker, APIKeyConfig
from src.lib_auth.jwt import (
    JWTClaim,
    JWTDecodeService,
    JWTException,
    decode_and_verify_jwt_token,
)


def make_api_key_checker(config: APIKeyConfig, app: str, method: str, endpoint: str):
    async def check(x_api_key: Annotated[str, Header()]):
        if x_api_key is None:
            raise ValueError("Missing X-API-Key header")
        api_key_checker = APIKeyChecker(config)
        try:
            api_key_checker.check(
                x_api_key, APIEndpoint(app=app, method=method, endpoint=endpoint)
            )
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid API key")

    return check


def get_authorization_token(
    cookie_jwt_token: Annotated[str | None, Cookie(alias="jwt_access_token")] = None,
    header_authorization: Annotated[
        str | None, Header(alias="X-Oly-Authorization")
    ] = None,
) -> str | None:
    # get from cookie
    jwt_access_token = cookie_jwt_token

    # otherwise get from header
    if not jwt_access_token:
        if not header_authorization:
            return None

        header_authorization_tokens = header_authorization.split(" ")
        if len(header_authorization_tokens) != 2:
            return None

        if header_authorization_tokens[0] != "Bearer":
            return None

        jwt_access_token = header_authorization_tokens[1]

    return jwt_access_token


def build_claim_authenticator(
    jwt_decode_service: JWTDecodeService,
    with_user_role_in: List[str] | None = None,
    with_organization_role: str | None = None,
):
    def get_verified_claim(
        jwt_access_token: Annotated[str | None, Depends(get_authorization_token)],
    ) -> JWTClaim:
        if not jwt_access_token:
            raise HTTPException(status_code=401, detail="Not Authorized")

        try:
            jwt_claim = decode_and_verify_jwt_token(
                jwt_access_token, jwt_decode_service
            )
        except JWTException:
            raise HTTPException(status_code=401, detail="Not Authorized")

        if with_user_role_in and jwt_claim.custom_claims.role not in with_user_role_in:
            raise HTTPException(status_code=403, detail="Forbidden")

        if (
            with_organization_role
            and jwt_claim.custom_claims.organization_role != with_organization_role
        ):
            raise HTTPException(status_code=403, detail="Forbidden")

        return jwt_claim

    return get_verified_claim
