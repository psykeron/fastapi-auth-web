from fastapi.testclient import TestClient

from src.apps.auth.app import app
from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import build_new_user
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.apps.auth.repository.users import UserRepository
from src.lib_auth.roles import OrganizationRole, UserRole

client = TestClient(app)


class TestUserCreate:
    PLATFORM_OWNER_EMAIL = "platform_owner@oly.co"
    PLATFORM_OWNER_PASSWORD = "test_password_123_$$%"

    NON_PLATFORM_OWNER_EMAIL = "non_platform_owner@oly.co"
    NON_PLATFORM_OWNER_PASSWORD = "test_password_123_$$%"

    async def add_platform_owner(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
    ):
        user = build_new_user(
            email=self.PLATFORM_OWNER_EMAIL,
            password=self.PLATFORM_OWNER_PASSWORD,
            role=UserRole.USER,
            first_name="Platform",
            last_name="Owner",
        )

        organization = Organization(
            name="Platform",
            description="Platform Owner",
            role=OrganizationRole.PLATFORM_OWNER,
        )
        user.activate()
        user.confirm(user.confirmation_token)
        await user_repository.save_user(user)
        saved_organization = await organizations_repository.create_organization(
            organization
        )
        saved_user = await user_repository.get_user_by_email(self.PLATFORM_OWNER_EMAIL)
        assert saved_user is not None

        saved_user.organization = saved_organization

        await user_repository.save_user(saved_user)

    async def add_platform_user(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
    ):
        user = build_new_user(
            email=self.NON_PLATFORM_OWNER_EMAIL,
            password=self.NON_PLATFORM_OWNER_PASSWORD,
            role=UserRole.USER,
            first_name="NotAPlatform",
            last_name="Owner",
        )

        organization = Organization(
            name="PlatformUser",
            description="Platform User",
            role=OrganizationRole.PLATFORM_USER,
        )
        user.activate()
        user.confirm(user.confirmation_token)
        await user_repository.save_user(user)
        saved_organization = await organizations_repository.create_organization(
            organization
        )
        saved_user = await user_repository.get_user_by_email(
            self.NON_PLATFORM_OWNER_EMAIL
        )
        assert saved_user is not None

        saved_user.organization = saved_organization

        await user_repository.save_user(saved_user)

    async def get_authorization_token_for_platform_owner(self) -> str:
        response = client.post(
            "/v1/login",
            json={
                "username": self.PLATFORM_OWNER_EMAIL,
                "password": self.PLATFORM_OWNER_PASSWORD,
                "grant_type": "password",
            },
        )

        return response.json()["access_token"]

    async def get_authorization_token_for_basic_user(self) -> str:
        response = client.post(
            "/v1/login",
            json={
                "username": self.NON_PLATFORM_OWNER_EMAIL,
                "password": self.NON_PLATFORM_OWNER_PASSWORD,
                "grant_type": "password",
            },
        )

        return response.json()["access_token"]

    async def test_create_new_user_without_authorization_header_returns_401(
        self,
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        response = client.post(
            "/v1/users",
            json={
                "email": email,
                "password": password,
                "confirm_password": password,
                "first_name": "Test",
                "last_name": "User",
            },
        )

        assert response.status_code == 401

    async def test_create_new_user_with_bad_authorization_header_returns_401(
        self,
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        response = client.post(
            "/v1/users",
            json={
                "email": email,
                "password": password,
                "confirm_password": password,
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"X-Oly-Authorization": "Bearer bad_token"},
        )

        assert response.status_code == 401

    async def test_create_new_user_with_non_platform_owner_authorization_header_returns_403(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await self.add_platform_user(user_repository, organizations_repository)
        access_token = await self.get_authorization_token_for_basic_user()

        email = "test@oly.co"
        password = "test_password_123_$$%"

        response = client.post(
            "/v1/users",
            json={
                "email": email,
                "password": password,
                "confirm_password": password,
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403

    async def test_create_new_user(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await self.add_platform_owner(user_repository, organizations_repository)
        access_token = await self.get_authorization_token_for_platform_owner()

        email = "test@oly.co"
        password = "test_password_123_$$%"

        response = client.post(
            "/v1/users",
            json={
                "email": email,
                "password": password,
                "confirm_password": password,
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "email": email}

    async def test_create_user_with_existing_email(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await self.add_platform_owner(user_repository, organizations_repository)
        access_token = await self.get_authorization_token_for_platform_owner()

        email = "test@oly.co"
        password = "test_password_123_$$%"

        data = {
            "email": email,
            "password": password,
            "confirm_password": password,
            "first_name": "Test",
            "last_name": "User",
        }

        # create a user
        assert (
            client.post(
                "/v1/users",
                json=data,
                headers={"X-Oly-Authorization": f"Bearer {access_token}"},
            ).status_code
            == 200
        )

        # try to create a user with the same email
        response = client.post(
            "/v1/users",
            json=data,
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "User already exists"}

    async def test_create_user_with_non_matching_passwords(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await self.add_platform_owner(user_repository, organizations_repository)
        access_token = await self.get_authorization_token_for_platform_owner()

        email = "test@oly.co"
        password = "test_password_123_$$%"

        # create a user
        response = client.post(
            "/v1/users",
            json={
                "email": email,
                "password": password,
                "confirm_password": password + "_random",
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400
        assert response.json() == {"detail": "Passwords do not match"}

    async def test_create_user_with_invalid_email(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await self.add_platform_owner(user_repository, organizations_repository)
        access_token = await self.get_authorization_token_for_platform_owner()
        password = "test_password_123_$$%"

        # create a user
        response = client.post(
            "/v1/users",
            json={
                "email": "",
                "password": password,
                "confirm_password": password,
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 400
