from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import SensitiveUser, build_new_user
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.apps.auth.repository.users import UserRepository
from src.lib_auth.roles import UserRole


class TestUserRepositoryUserCreation:
    def build_user(self) -> SensitiveUser:
        return SensitiveUser(
            id="abc-abc-abc",
            email="abc@abc.com",
            hashed_password="a_hashed_password",
            is_activated=False,
            is_confirmed=False,
            confirmation_token="a_confirmation_token",
            role=UserRole.USER,
        )

    async def test_created_user_has_correct_email(
        self, user_repository: UserRepository
    ):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.email == "abc@abc.com"

    async def test_created_user_has_correct_id(self, user_repository: UserRepository):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.id == "abc-abc-abc"

    async def test_created_user_has_correct_hashed_password(
        self, user_repository: UserRepository
    ):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_sensitive_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.hashed_password == "a_hashed_password"

    async def test_created_user_has_correct_role(self, user_repository: UserRepository):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.role == UserRole.USER

    async def test_created_user_has_correct_confirmation_token(
        self, user_repository: UserRepository
    ):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_sensitive_user_by_email("abc@abc.com")
        assert (
            fetched_user and fetched_user.confirmation_token == "a_confirmation_token"
        )

    async def test_created_user_has_correct_activation_status(
        self, user_repository: UserRepository
    ):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.is_activated is False

    async def test_created_user_has_correct_confirmation_status(
        self, user_repository: UserRepository
    ):
        user = self.build_user()
        await user_repository.save_user(user)
        fetched_user = await user_repository.get_user_by_email("abc@abc.com")
        assert fetched_user and fetched_user.is_confirmed is False


class TestUserRepositoryUserOrganizationRelations:
    async def test_user_is_correctly_associated_with_organization(
        self,
        async_session: AsyncSession,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        # create an organization
        organization = Organization(
            name="abc",
            description="abc",
        )
        saved_organization = await organizations_repository.create_organization(
            organization
        )

        # create a user
        user = build_new_user(
            email="abc@abc.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )
        await user_repository.save_user(user)

        # check that the user is not associated with any organization
        assert user.organization is None

        # associate user with organization
        user.organization = saved_organization
        await user_repository.save_user(user)

        user_id = user.id
        # rollback to clear the session
        await async_session.rollback()

        # fetch the user
        fetched_user = await user_repository.get_user_by_id(str(user_id))

        assert fetched_user is not None
        assert fetched_user.organization is not None
        assert fetched_user.organization.id == saved_organization.id

    async def test_user_is_correctly_removed_from_organization(
        self,
        async_session: AsyncSession,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        # create an organization
        organization = Organization(
            name="abc",
            description="abc",
        )
        saved_organization = await organizations_repository.create_organization(
            organization
        )

        # create a user
        user = build_new_user(
            email="abc@abc.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )
        await user_repository.save_user(user)
        user_id = user.id

        # associate user with organization
        user.organization = saved_organization
        await user_repository.save_user(user)
        assert user.organization.id == saved_organization.id

        # remove user from organization
        user.organization = None
        await user_repository.save_user(user)

        # rollback to clear the session
        await async_session.rollback()

        # fetch the user
        fetched_user = await user_repository.get_user_by_id(str(user_id))
        assert fetched_user is not None
        assert fetched_user.organization is None


class TestUserRepositoryGetUsers:
    async def test_get_users_returns_correct_users(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)

        users = await user_repository.get_users()
        assert len(users) == 2
        assert user1.id == users[0].id
        assert user2.id == users[1].id

    async def test_get_users_returns_correct_users_with_limit(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)

        users = await user_repository.get_users(limit=1)
        assert len(users) == 1
        assert user1.id == users[0].id

    async def test_get_users_returns_correct_users_with_offset(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)

        users = await user_repository.get_users(offset=1)
        assert len(users) == 1
        assert user2.id == users[0].id

    async def test_get_users_returns_correct_users_with_limit_and_offset(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        user3 = build_new_user(
            email="user3@email.com",
            password="sometsomething!@#12345A",
            role=UserRole.USER,
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)
        await user_repository.save_user(user3)

        users = await user_repository.get_users(limit=2, offset=1)

        assert len(users) == 2
        assert user2.id == users[0].id
        assert user3.id == users[1].id

    async def test_get_users_returns_correct_users_with_username_contains(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1withaname@email.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2withaname@oly.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        user3 = build_new_user(
            email="user3@oly.com", password="something!@#12345A", role=UserRole.USER
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)
        await user_repository.save_user(user3)

        users = await user_repository.get_users(username_contains="oly")

        assert len(users) == 2
        assert user2.id == users[0].id
        assert user3.id == users[1].id

    async def test_get_users_with_username_contains_is_case_insensitive(
        self,
        user_repository: UserRepository,
        ensure_clean_db: None,
    ):
        user1 = build_new_user(
            email="user1withaname@email.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2withaname@OLy.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        user3 = build_new_user(
            email="user3@oly.com", password="something!@#12345A", role=UserRole.USER
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)
        await user_repository.save_user(user3)

        users = await user_repository.get_users(username_contains="olY")

        assert len(users) == 2
        assert user2.id == users[0].id
        assert user3.id == users[1].id

    async def test_get_users_returns_correct_users_with_organization_id(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        organization1 = Organization(
            name="abc",
            description="abc",
        )

        organization2 = Organization(
            name="def",
            description="def",
        )

        saved_organization_1 = await organizations_repository.create_organization(
            organization1
        )
        saved_organization_2 = await organizations_repository.create_organization(
            organization2
        )

        user1 = build_new_user(
            email="user1@org1.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        user2 = build_new_user(
            email="user2@org2.com",
            password="something!@#12345A",
            role=UserRole.USER,
        )

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)

        user1.organization = saved_organization_1
        user2.organization = saved_organization_2

        await user_repository.save_user(user1)
        await user_repository.save_user(user2)

        users = await user_repository.get_users(
            organization_id=str(saved_organization_1.id)
        )

        assert len(users) == 1
        assert user1.id == users[0].id
