from typing import AsyncGenerator

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.apps.auth.config import get_config
from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import User
from src.apps.auth.orm.mappers import start_mappers
from src.apps.auth.repository.organizations import (
    OrganizationsRepository,
    SQLOrganizationsRepository,
)
from src.apps.auth.repository.users import SQLUserRepository, UserRepository


@pytest.fixture(scope="function")
def async_sql_engine() -> AsyncEngine:
    start_mappers()
    return create_async_engine(get_config().database.url)


@pytest.fixture(scope="function")
def session_maker(async_sql_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        expire_on_commit=False, class_=AsyncSession, bind=async_sql_engine
    )


@pytest.fixture(scope="function")
async def async_session(session_maker) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


async def __cleanup_db(session: AsyncSession):
    await session.execute(delete(User))
    await session.execute(delete(Organization))
    await session.commit()
    await session.rollback()


@pytest.fixture(scope="function")
async def ensure_clean_db(async_session: AsyncSession) -> None:
    await __cleanup_db(async_session)


@pytest.fixture(scope="function")
async def user_repository(
    async_session: AsyncSession, ensure_clean_db: None
) -> UserRepository:
    return SQLUserRepository(async_session)


@pytest.fixture(scope="function")
async def organizations_repository(
    async_session: AsyncSession, ensure_clean_db: None
) -> OrganizationsRepository:
    return SQLOrganizationsRepository(async_session)
