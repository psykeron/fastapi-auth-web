from typing import Annotated, Any, List, Literal, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.apps.auth.config import AuthDomainConfig
from src.lib_auth.jwt import JWTSigningService, build_jwt_claim, create_jwt_token

from ..app import app
from ..dependencies import (
    get_authenticated_user,
    get_authentication_domains,
    jwt_signing_service,
    user_repository,
)
from ..models.user import AuthenticationException, SensitiveUser, User
from ..repository.users import UserRepository


class OAuth2Request(BaseModel):
    grant_type: str
    scopes: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class OAuth2PasswordRequest(BaseModel):
    grant_type: Literal["password"]
    scopes: Optional[str] = None
    username: str
    password: str


class OAuth2ClientCredentialsRequest(BaseModel):
    grant_type: Literal["client_credentials"]
    scopes: Optional[str] = None
    client_id: str
    client_secret: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]


class SimpleSuccessResponse(BaseModel):
    status: Literal["ok"]


class MeResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    is_confirmed: bool


@app.exception_handler(AuthenticationException)
async def channel_already_exists_handler(
    request: Request, exc: AuthenticationException
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": str(exc)},
    )


def get_cookie_domain(
    origin: str, allowed_domains: List[AuthDomainConfig]
) -> AuthDomainConfig | None:
    if not origin:
        return None

    if not allowed_domains:
        return None

    # get the domain from the origin
    [origin_protocol, origin_domain_with_port] = origin.split("://")
    origin_domain = origin_domain_with_port.split(":")[0]

    origin_with_protocol = f"{origin_protocol}://{origin_domain}"

    # check if the origin domain is in the allowed domains
    for allowed_domain in allowed_domains:
        if origin_with_protocol == allowed_domain.origin:
            return allowed_domain

    return None


@app.post("/v1/login")
async def login(
    request: OAuth2Request,
    user_repository: Annotated[UserRepository, Depends(user_repository)],
    jwt_signing_service: Annotated[JWTSigningService, Depends(jwt_signing_service)],
    allowed_cookie_domains: Annotated[
        List[AuthDomainConfig], Depends(get_authentication_domains)
    ],
    as_cookie: bool = False,
    http_origin: Annotated[str, Header(alias="Origin")] = "",
) -> AccessTokenResponse | SimpleSuccessResponse | Any:
    user: SensitiveUser | None = None
    password_request: OAuth2PasswordRequest | None = None

    if request.grant_type != "password":
        raise HTTPException(
            status_code=400, detail=f"Unsupported grant type: {request.grant_type}"
        )

    password_request = OAuth2PasswordRequest(**request.model_dump())
    user = await user_repository.get_sensitive_user_by_email(password_request.username)

    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    user.authenticate(password_request.password)

    twenty_four_hours = 24
    seconds_in_an_hour = 60 * 60
    days = 2
    expiry_in_seconds = twenty_four_hours * seconds_in_an_hour * days
    token = create_jwt_token(
        payload=build_jwt_claim(
            user_id=user.id,  # type: ignore
            role=user.role,
            issuer="oly-auth-silo-1",
            organization_id=user.organization.id if user.organization else None,
            organization_role=user.organization.role if user.organization else None,
            expire_in_seconds=expiry_in_seconds,
        ),
        signing_service=jwt_signing_service,
    )

    if as_cookie:
        cookie_domain_config = get_cookie_domain(http_origin, allowed_cookie_domains)

        if not cookie_domain_config:
            raise HTTPException(
                status_code=400, detail="Cannot set cookie for this origin"
            )

        response = JSONResponse(content=SimpleSuccessResponse(status="ok").model_dump())
        response.set_cookie(
            key="jwt_access_token",
            value=token,
            httponly=True,
            max_age=expiry_in_seconds,
            samesite="none",
            secure=cookie_domain_config.cookie_is_secure,
            domain=cookie_domain_config.cookie_domain,
        )
        return response

    return AccessTokenResponse(access_token=token, token_type="bearer")


@app.post("/v1/logout")
async def logout(
    allowed_cookie_domains: Annotated[
        List[AuthDomainConfig], Depends(get_authentication_domains)
    ],
    http_origin: Annotated[str, Header(alias="Origin")] = "",
) -> SimpleSuccessResponse | Any:
    response = JSONResponse(content=SimpleSuccessResponse(status="ok").model_dump())
    cookie_domain_config = get_cookie_domain(http_origin, allowed_cookie_domains)
    if not cookie_domain_config:
        return response
    else:
        response.delete_cookie(
            key="jwt_access_token",
            httponly=True,
            samesite="none",
            secure=cookie_domain_config.cookie_is_secure,
            domain=cookie_domain_config.cookie_domain,
        )
    return response


@app.get("/v1/me")
async def me(
    authenticated_user: Annotated[User, Depends(get_authenticated_user)]
) -> User | Any:
    return authenticated_user
