from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models.user import SensitiveUser, User


class UserRepository(Protocol):
    async def get_user_by_email(self, email: str) -> User | None: ...

    async def get_user_by_id(self, id: str) -> User | None: ...

    async def get_sensitive_user_by_email(self, email: str) -> SensitiveUser | None: ...

    async def get_sensitive_user_by_id(self, id: str) -> SensitiveUser | None: ...

    async def get_users(
        self,
        username_contains: str | None = None,
        organization_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]: ...

    async def save_user(self, user: SensitiveUser | User) -> None: ...

    async def delete_user(self, user: SensitiveUser | User) -> None: ...


class SQLUserRepository:
    def __init__(self, session: AsyncSession):
        self.__async_session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.__async_session.execute(
            select(User)
            .options(joinedload(User.organization))  # type: ignore[arg-type]
            .filter_by(email=email)
        )

        return result.scalar_one_or_none()

    async def get_user_by_id(self, id: str) -> User | None:
        query = (
            select(User)
            .options(joinedload(User.organization))  # type: ignore[arg-type]
            .filter_by(id=id)
        )

        result = await self.__async_session.execute(query)
        return result.scalar_one_or_none()

    async def get_sensitive_user_by_email(self, email: str) -> SensitiveUser | None:
        result = await self.__async_session.execute(
            select(SensitiveUser)
            .options(joinedload(SensitiveUser.organization))  # type: ignore[arg-type]
            .filter_by(email=email)
        )
        return result.scalar_one_or_none()

    async def get_sensitive_user_by_id(self, id: str) -> SensitiveUser | None:
        result = await self.__async_session.execute(
            select(SensitiveUser)
            .options(joinedload(SensitiveUser.organization))  # type: ignore[arg-type]
            .filter_by(id=id)
        )
        return result.scalar_one_or_none()

    async def get_users(
        self,
        username_contains: str | None = None,
        organization_id: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[User]:
        query = select(User)

        if username_contains:
            query = query.filter(
                User.email.icontains(username_contains)  # type: ignore[union-attr]
            )

        if organization_id:
            query = query.filter(
                User.organization_id == organization_id  # type: ignore[attr-defined]
            )

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        query = query.options(joinedload(User.organization))  # type: ignore[arg-type]
        query = query.order_by(User.created_at)  # type: ignore[arg-type]

        result = await self.__async_session.execute(query)

        return list(result.scalars().all())

    async def save_user(self, user: SensitiveUser | User) -> None:
        self.__async_session.add(user)
        await self.__async_session.commit()

    async def delete_user(self, user: SensitiveUser | User) -> None:
        raise NotImplementedError
