from datetime import datetime

from src.apps.auth.models.organization import Organization
from src.lib_auth.roles import OrganizationRole


class TestPartialOrganizationWithDefaults:
    def build_organization(self) -> Organization:
        return Organization(
            name="Test Organization",
            description="Test Description",
        )

    def test_organization_id_is_none(self):
        organization = self.build_organization()
        assert organization.id is None

    def test_organization_created_at_is_none(self):
        organization = self.build_organization()
        assert organization.created_at is None

    def test_organization_updated_at_is_none(self):
        organization = self.build_organization()
        assert organization.updated_at is None

    def test_organization_name_is_correct(self):
        organization = self.build_organization()
        assert organization.name == "Test Organization"

    def test_organization_description_is_correct(self):
        organization = self.build_organization()
        assert organization.description == "Test Description"

    def test_organization_role_is_correct(self):
        organization = self.build_organization()
        assert organization.role == OrganizationRole.PLATFORM_USER


class TestOrganizationWithEverythingSet:
    def build_organization(self) -> Organization:
        return Organization(
            name="Test Organization",
            description="Test Description",
            role=OrganizationRole.PLATFORM_OWNER,
            id="test-id",
            created_at=datetime(2021, 1, 1),
            updated_at=datetime(2021, 1, 1),
        )

    def test_organization_id_is_correct(self):
        organization = self.build_organization()
        assert organization.id == "test-id"

    def test_organization_created_at_is_correct(self):
        organization = self.build_organization()
        assert organization.created_at == datetime(2021, 1, 1)

    def test_organization_updated_at_is_correct(self):
        organization = self.build_organization()
        assert organization.updated_at == datetime(2021, 1, 1)

    def test_organization_name_is_correct(self):
        organization = self.build_organization()
        assert organization.name == "Test Organization"

    def test_organization_description_is_correct(self):
        organization = self.build_organization()
        assert organization.description == "Test Description"

    def test_organization_role_is_correct(self):
        organization = self.build_organization()
        assert organization.role == OrganizationRole.PLATFORM_OWNER
