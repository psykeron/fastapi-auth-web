from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import build_new_user
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.apps.auth.repository.users import UserRepository
from src.lib_auth.roles import OrganizationRole, UserRole

PLATFORM_OWNER_EMAIL = "platform_owner@oly.co"
PLATFORM_OWNER_PASSWORD = "test_password_123_$$%"

NON_PLATFORM_OWNER_EMAIL = "non_platform_owner@oly.co"
NON_PLATFORM_OWNER_PASSWORD = "test_password_123_$$%"


async def add_platform_owner(
    user_repository: UserRepository,
    organizations_repository: OrganizationsRepository,
):
    user = build_new_user(
        email=PLATFORM_OWNER_EMAIL,
        password=PLATFORM_OWNER_PASSWORD,
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
    saved_user = await user_repository.get_user_by_email(PLATFORM_OWNER_EMAIL)
    assert saved_user is not None

    saved_user.organization = saved_organization

    await user_repository.save_user(saved_user)


async def add_platform_user(
    user_repository: UserRepository,
    organizations_repository: OrganizationsRepository,
):
    user = build_new_user(
        email=NON_PLATFORM_OWNER_EMAIL,
        password=NON_PLATFORM_OWNER_PASSWORD,
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
    saved_user = await user_repository.get_user_by_email(NON_PLATFORM_OWNER_EMAIL)
    assert saved_user is not None

    saved_user.organization = saved_organization

    await user_repository.save_user(saved_user)


async def get_authorization_token_for_platform_owner(auth_client) -> str:
    response = auth_client.post(
        "/v1/login",
        json={
            "username": PLATFORM_OWNER_EMAIL,
            "password": PLATFORM_OWNER_PASSWORD,
            "grant_type": "password",
        },
    )

    return response.json()["access_token"]


async def get_authorization_token_for_basic_user(auth_client) -> str:
    response = auth_client.post(
        "/v1/login",
        json={
            "username": NON_PLATFORM_OWNER_EMAIL,
            "password": NON_PLATFORM_OWNER_PASSWORD,
            "grant_type": "password",
        },
    )

    return response.json()["access_token"]
