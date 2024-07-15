from fastapi.testclient import TestClient

from src.apps.auth.app import app
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.apps.auth.repository.users import UserRepository
from src.lib_auth.roles import OrganizationRole
from tests.test_utils.user import (
    add_platform_owner,
    add_platform_user,
    get_authorization_token_for_basic_user,
    get_authorization_token_for_platform_owner,
)

client = TestClient(app, raise_server_exceptions=True)


class TestOrganizationCreate:
    async def test_create_new_organization_with_non_platform_owner_authorization_header_returns_403(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_user(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_basic_user(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403

    async def test_create_new_organization(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == "Test Organization"
        assert result["description"] == "A test organization"
        assert result["role"] == OrganizationRole.PLATFORM_USER.value
        assert result["id"] is not None
        assert result["created_at"] is not None
        assert result["updated_at"] is not None

    async def test_create_organization_with_existing_name_raises_409(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 409


class TestOrganizationUpdate:
    async def test_update_organization_with_non_platform_owner_authorization_header_returns_403(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_user(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_basic_user(client)

        response = client.put(
            "/v1/organizations",
            json={
                "id": "abc-abc-abc",
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403

    async def test_update_organization(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        result = response.json()
        assert response.status_code == 200

        response = client.put(
            "/v1/organizations",
            json={
                "id": result["id"],
                "name": "Updated Test Organization",
                "description": "An updated test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        result = response.json()
        assert response.status_code == 200
        assert result["name"] == "Updated Test Organization"
        assert result["description"] == "An updated test organization"
        assert result["role"] == OrganizationRole.PLATFORM_USER.value
        assert result["id"] is not None
        assert result["created_at"] is not None
        assert result["updated_at"] is not None

    async def test_update_non_existing_organization_raises_404(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.put(
            "/v1/organizations",
            json={
                "id": "abc-abc-abc",
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 404


class TestOrganizationList:
    async def test_list_organization_with_non_platform_owner_authorization_header_returns_403(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_user(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_basic_user(client)

        response = client.get(
            "/v1/organizations",
            params={},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 403

    async def test_list_organizations(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response = client.get(
            "/v1/organizations",
            params={},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        result = response.json()

        # remove the platform owner organization
        result = [
            org
            for org in response.json()
            if org["role"] != OrganizationRole.PLATFORM_OWNER.value
        ]

        assert response.status_code == 200
        assert len(result) == 1
        assert result[0]["name"] == "Test Organization"

    async def test_list_organizations_with_limit_and_offset(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization 1",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization 2",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response_offset_0 = client.get(
            "/v1/organizations",
            params={"limit": 1, "offset": 0},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response_offset_1 = client.get(
            "/v1/organizations",
            params={"limit": 1, "offset": 1},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response_offset_2 = client.get(
            "/v1/organizations",
            params={"limit": 1, "offset": 2},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        assert response_offset_0.status_code == 200
        assert response_offset_1.status_code == 200
        assert response_offset_2.status_code == 200

        result_offset_0 = response_offset_0.json()
        result_offset_1 = response_offset_1.json()
        result_offset_2 = response_offset_2.json()

        assert len(result_offset_0) == 1
        assert len(result_offset_1) == 1
        assert len(result_offset_2) == 1

        combined_results = result_offset_0 + result_offset_1 + result_offset_2

        result_org_1 = next(
            (org for org in combined_results if org["name"] == "Test Organization 1"),
            None,
        )
        result_org_2 = next(
            (org for org in combined_results if org["name"] == "Test Organization 2"),
            None,
        )
        result_org_platform_owner = next(
            (
                org
                for org in combined_results
                if org["role"] == OrganizationRole.PLATFORM_OWNER.value
            ),
            None,
        )

        assert result_org_1 is not None
        assert result_org_2 is not None
        assert result_org_platform_owner is not None

    async def test_list_organizations_with_name_contains(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        await add_platform_owner(user_repository, organizations_repository)
        access_token = await get_authorization_token_for_platform_owner(client)

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization 1",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response = client.post(
            "/v1/organizations",
            json={
                "name": "Test Organization 2",
                "description": "A test organization",
                "role": OrganizationRole.PLATFORM_USER.value,
            },
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response = client.get(
            "/v1/organizations",
            params={"name_contains": "1"},
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        result = response.json()
        assert response.status_code == 200
        assert len(result) == 1
        assert result[0]["name"] == "Test Organization 1"
