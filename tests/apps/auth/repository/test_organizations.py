import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.auth.models.organization import Organization
from src.apps.auth.repository.organizations import (
    OrganizationExistsError,
    OrganizationNotFoundError,
    OrganizationsRepository,
)
from src.lib_auth.roles import OrganizationRole


class TestOrganizationRepositoryOrganizationCreation:
    async def test_default_successful_creation(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            name="Test Organization",
            description="Test Description",
        )

        saved_organization = await organizations_repository.create_organization(
            organization
        )

        assert saved_organization.id is not None
        assert saved_organization.name == "Test Organization"
        assert saved_organization.description == "Test Description"
        assert saved_organization.role == OrganizationRole.PLATFORM_USER
        assert saved_organization.created_at is not None
        assert saved_organization.updated_at is not None

    async def test_full_successful_creation(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            name="Test Organization",
            description="Test Description",
            role=OrganizationRole.PLATFORM_OWNER,
        )

        saved_organization = await organizations_repository.create_organization(
            organization
        )

        assert saved_organization.id is not None
        assert saved_organization.name == "Test Organization"
        assert saved_organization.description == "Test Description"
        assert saved_organization.role == OrganizationRole.PLATFORM_OWNER
        assert saved_organization.created_at is not None
        assert saved_organization.updated_at is not None

    async def test_creation_with_id_raises_error(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            id="abc-abc-abc",
            name="Test Organization",
            description="Test Description",
        )

        with pytest.raises(ValueError):
            await organizations_repository.create_organization(organization)

    async def test_creation_with_existing_name_raises_error(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            name="Test Organization",
            description="Test Description",
        )

        await organizations_repository.create_organization(organization)

        with pytest.raises(
            OrganizationExistsError, match="Organization with this name already exists"
        ):
            await organizations_repository.create_organization(
                Organization(name="Test Organization", description="Some Description")
            )


class TestOrganizationRepositoryOrganizationUpdate:
    async def test_update_of_existing(
        self,
        async_session: AsyncSession,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        organization = Organization(
            name="Test Organization",
            description="Test Description",
        )

        saved_organization = await organizations_repository.create_organization(
            organization
        )

        saved_organization.name = "Updated Name"
        saved_organization.description = "Updated Description"

        updated_organization = await organizations_repository.update_organization(
            saved_organization
        )

        assert updated_organization.id == saved_organization.id
        assert updated_organization.name == "Updated Name"
        assert updated_organization.description == "Updated Description"
        assert updated_organization.role == OrganizationRole.PLATFORM_USER
        assert updated_organization.created_at is not None
        assert updated_organization.updated_at is not None

    async def test_update_non_existing(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            id=uuid.uuid4().hex,
            name="Test Organization",
            description="Test Description",
        )

        with pytest.raises(
            OrganizationNotFoundError,
            match=f"Organization {organization.id} does not exist",
        ):
            await organizations_repository.update_organization(organization)


class TestOrganizationRepositoryOrganizationGet:
    async def test_get_existing(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization = Organization(
            name="Test Organization",
            description="Test Description",
        )

        saved_organization = await organizations_repository.create_organization(
            organization
        )

        retrieved_organization = await organizations_repository.get_organization(
            str(saved_organization.id)
        )

        assert retrieved_organization
        assert retrieved_organization.id == saved_organization.id
        assert retrieved_organization.name == "Test Organization"
        assert retrieved_organization.description == "Test Description"
        assert retrieved_organization.role == OrganizationRole.PLATFORM_USER
        assert retrieved_organization.created_at is not None
        assert retrieved_organization.updated_at is not None

    async def test_get_without_id_raises_exception(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        with pytest.raises(ValueError, match="Organization id is required"):
            await organizations_repository.get_organization("")

    async def test_get_non_existing(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        retrieved_organization = await organizations_repository.get_organization("abc")
        assert retrieved_organization is None

    async def test_get_all_organizations(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization1 = Organization(
            name="Test Organization 1",
            description="Test Description 1",
        )

        organization2 = Organization(
            name="Test Organization 2",
            description="Test Description 2",
        )

        await organizations_repository.create_organization(organization1)
        await organizations_repository.create_organization(organization2)

        organizations = await organizations_repository.get_organizations()

        assert len(organizations) == 2

        assert organizations[0].name == "Test Organization 1"
        assert organizations[0].description == "Test Description 1"
        assert organizations[0].role == OrganizationRole.PLATFORM_USER
        assert organizations[0].created_at is not None
        assert organizations[0].updated_at is not None

        assert organizations[1].name == "Test Organization 2"
        assert organizations[1].description == "Test Description 2"
        assert organizations[1].role == OrganizationRole.PLATFORM_USER
        assert organizations[1].created_at is not None
        assert organizations[1].updated_at is not None

    async def test_get_organizations_with_limit_and_offset(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        organization1 = Organization(
            name="Test Organization 1",
            description="Test Description 1",
        )

        organization2 = Organization(
            name="Test Organization 2",
            description="Test Description 2",
        )

        organization3 = Organization(
            name="Test Organization 3",
            description="Test Description 3",
        )

        await organizations_repository.create_organization(organization1)
        await organizations_repository.create_organization(organization2)
        await organizations_repository.create_organization(organization3)

        organizations = await organizations_repository.get_organizations(
            limit=1, offset=1
        )

        assert len(organizations) == 1

        assert organizations[0].name == "Test Organization 2"
        assert organizations[0].description == "Test Description 2"
        assert organizations[0].role == OrganizationRole.PLATFORM_USER
        assert organizations[0].created_at is not None
        assert organizations[0].updated_at is not None

    async def test_get_organizations_with_name_contains(
        self, organizations_repository: OrganizationsRepository, ensure_clean_db: None
    ):
        search_term = "ucci"

        # will match
        organization1 = Organization(
            name="Gucci",
            description="Test Description 1",
        )

        # won't match
        organization2 = Organization(
            name="Dior",
            description="Test Description 2",
        )

        # will match
        organization3 = Organization(
            name="Gucci Dior",
            description="Test Description 3",
        )

        # will match
        organization4 = Organization(
            name="GuCci Louis",
            description="Test Description 3",
        )

        organization1 = await organizations_repository.create_organization(
            organization1
        )
        organization2 = await organizations_repository.create_organization(
            organization2
        )
        organization3 = await organizations_repository.create_organization(
            organization3
        )
        organization4 = await organizations_repository.create_organization(
            organization4
        )

        organizations = await organizations_repository.get_organizations(
            name_contains=search_term
        )

        assert len(organizations) == 3

        result_org_1 = next(
            (org for org in organizations if org.id == organization1.id), None
        )
        assert result_org_1

        result_org_3 = next(
            (org for org in organizations if org.id == organization3.id), None
        )
        assert result_org_3

        result_org_4 = next(
            (org for org in organizations if org.id == organization4.id), None
        )
        assert result_org_4
