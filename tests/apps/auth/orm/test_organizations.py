from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.auth.models.organization import Organization
from src.lib_auth.roles import OrganizationRole


class TestOrganizationSave:
    async def test_organization_is_saved_correctly(
        self, async_session: AsyncSession, ensure_clean_db: None
    ):
        organization = Organization(
            id="test-id",
            name="Test Organization",
            description="Test Description",
            role=OrganizationRole.PLATFORM_OWNER,
        )

        async_session.add(organization)
        await async_session.commit()

        result = await async_session.execute(select(Organization))

        result_organizations = result.scalars().all()
        assert len(result_organizations) == 1

        result_organization = result_organizations[0]
        assert result_organization.id == "test-id"
        assert result_organization.name == "Test Organization"
        assert result_organization.description == "Test Description"
        assert result_organization.role == OrganizationRole.PLATFORM_OWNER
        assert result_organization.created_at is not None
        assert result_organization.updated_at is not None
