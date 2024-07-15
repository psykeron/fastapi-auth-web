from typing import Annotated, AsyncGenerator, List

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.apps.auth.models.user import User
from src.apps.auth.repository.organizations import (
    OrganizationsRepository,
    SQLOrganizationsRepository,
)
from src.apps.auth.repository.users import SQLUserRepository, UserRepository
from src.lib_auth.jwt import (
    JWTClaim,
    JWTDecodeService,
    JWTSigningService,
    RSA256JWTDecodeService,
    RSA256JWTSigningService,
)
from src.lib_auth.roles import OrganizationRole
from src.lib_fastapi.auth import build_claim_authenticator

from .config import AuthDomainConfig, get_config


def async_sql_engine() -> AsyncEngine:
    return create_async_engine(get_config().database.url)


def session_maker(
    engine: Annotated[AsyncEngine, Depends(async_sql_engine)]
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(expire_on_commit=False, class_=AsyncSession, bind=engine)


async def async_session(
    make_session: Annotated[async_sessionmaker[AsyncSession], Depends(session_maker)]
) -> AsyncGenerator[AsyncSession, None]:
    async with make_session() as session:
        yield session


def user_repository(
    session: Annotated[AsyncSession, Depends(async_session)]
) -> UserRepository:
    return SQLUserRepository(session)


def organizations_repository(
    session: Annotated[AsyncSession, Depends(async_session)]
) -> OrganizationsRepository:
    return SQLOrganizationsRepository(session)


def jwt_signing_service() -> JWTSigningService:
    private_key_config = get_config().private_key
    return RSA256JWTSigningService(
        private_key_pem=private_key_config.key,  # type:ignore
        private_key_password=private_key_config.password,  # type:ignore
    )


def jwt_decode_service() -> JWTDecodeService:
    public_key_config = get_config().public_key
    return RSA256JWTDecodeService(public_key_pem=public_key_config.key)  # type: ignore


def get_authentication_domains() -> List[AuthDomainConfig] | None:
    return get_config().domains


async def get_authenticated_user(
    verified_claim: Annotated[
        JWTClaim, Depends(build_claim_authenticator(jwt_decode_service()))
    ],
    user_repository: Annotated[UserRepository, Depends(user_repository)],
) -> User:
    user_id = verified_claim.custom_claims.user_id
    user = await user_repository.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_activated and not user.is_confirmed:
        raise HTTPException(status_code=403, detail="User is not active")

    return user


async def get_authenticated_platform_owner(
    authenticated_user: Annotated[User, Depends(get_authenticated_user)]
) -> User:
    if not authenticated_user.organization:
        raise HTTPException(status_code=403, detail="Forbidden")

    if authenticated_user.organization.role != OrganizationRole.PLATFORM_OWNER:
        raise HTTPException(status_code=403, detail="Forbidden")

    return authenticated_user
