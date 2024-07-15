import uuid
from typing import List, Protocol

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.organization import Organization


class OrganizationExistsError(Exception):
    pass


class OrganizationNotFoundError(Exception):
    pass


class OrganizationsRepository(Protocol):
    async def get_organizations(
        self,
        name_contains: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[Organization]:
        pass

    async def get_organization(self, organization_id: str) -> Organization | None:
        pass

    async def update_organization(self, organization: Organization) -> Organization:
        pass

    async def create_organization(self, organization: Organization) -> Organization:
        pass


class SQLOrganizationsRepository(OrganizationsRepository):
    def __init__(self, session: AsyncSession):
        self.__async_session = session

    async def get_organizations(
        self,
        name_contains: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> List[Organization]:
        query = select(Organization)

        if name_contains:
            # search by name but ignore case
            query = query.filter(Organization.name.ilike(f"%{name_contains}%"))  # type: ignore[attr-defined]

        if limit:
            query = query.limit(limit)

        if offset:
            query = query.offset(offset)

        query = query.order_by(Organization.created_at)  # type: ignore[arg-type]

        result = await self.__async_session.execute(query)

        return list(result.scalars().all())

    async def get_organization(self, organization_id: str) -> Organization | None:
        if not organization_id:
            raise ValueError("Organization id is required")

        query = select(Organization).filter_by(id=organization_id)

        query = query.order_by(Organization.created_at)  # type: ignore[arg-type]

        result = await self.__async_session.execute(query)

        return result.scalar_one_or_none()

    async def update_organization(self, organization: Organization) -> Organization:
        if not organization.id:
            raise ValueError("Organization id is required")

        existing_organization = await self.get_organization(organization.id)
        if not existing_organization:
            raise OrganizationNotFoundError(
                f"Organization {organization.id} does not exist"
            )

        existing_organization.name = organization.name
        existing_organization.description = organization.description
        existing_organization.role = organization.role

        self.__async_session.add(existing_organization)
        await self.__async_session.commit()
        await self.__async_session.refresh(existing_organization)

        return existing_organization

    async def create_organization(self, organization: Organization) -> Organization:
        if organization.id:
            raise ValueError("Organization id should not be provided")

        organization.id = uuid.uuid4().hex
        try:
            self.__async_session.add(organization)
            await self.__async_session.commit()
        except IntegrityError as e:
            raise OrganizationExistsError(
                "Organization with this name already exists"
            ) from e

        await self.__async_session.refresh(organization)

        return organization
