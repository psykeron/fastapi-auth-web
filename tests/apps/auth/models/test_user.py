import pytest

from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import (
    InvalidConfirmationTokenException,
    InvalidEmailException,
    NaivePasswordStrengthChecker,
    PasswordNotStrongException,
    SensitiveUser,
    build_new_user,
)
from src.lib_auth.password import verify_password
from src.lib_auth.roles import OrganizationRole, UserRole


class TestBasicPasswordStrengthChecker:
    def is_password_strong(self, password: str) -> bool:
        return NaivePasswordStrengthChecker.check(password)

    def test_password_is_strong(self):
        assert self.is_password_strong("StrongPassword123!@#") is True

    def test_empty_password_is_weak(self):
        assert self.is_password_strong("") is False

    def test_password_without_digit_is_weak(self):
        assert self.is_password_strong("w" * 16 + "!@#") is False

    def test_password_without_symbol_is_weak(self):
        assert self.is_password_strong("w" * 16 + "123") is False

    def test_password_with_less_than_16_characters_is_weak(self):
        assert self.is_password_strong("abc123!@#") is False


class TestUserCreation:
    @pytest.fixture(scope="class")
    def valid_user(self) -> SensitiveUser:
        return build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

    def test_valid_user_id_is_correct(self, valid_user: SensitiveUser):
        assert valid_user.id is not None

    def test_valid_user_email_is_correct(self, valid_user: SensitiveUser):
        assert valid_user.email == "abc@abc.com"

    def test_valid_user_password_is_hashed(self, valid_user: SensitiveUser):
        assert verify_password("StrongPassword123!@#", valid_user.hashed_password)

    def test_valid_user_role_is_correct(self, valid_user: SensitiveUser):
        assert valid_user.role == UserRole.USER

    def test_valid_user_is_not_activated(self, valid_user: SensitiveUser):
        assert valid_user.is_activated is False

    def test_valid_user_is_not_confirmed(self, valid_user: SensitiveUser):
        assert valid_user.is_confirmed is False

    def test_valid_user_does_not_have_organization(self, valid_user: SensitiveUser):
        assert valid_user.organization is None

    def test_invalid_password_raises_exception(self):
        with pytest.raises(PasswordNotStrongException):
            build_new_user(
                email="abc@abc.com", password="WeakPassword", role=UserRole.USER
            )

    def test_invalid_email_raises_exception(self):
        with pytest.raises(InvalidEmailException):
            build_new_user(
                email="", password="StrongPassword123!@#", role=UserRole.USER
            )


class TestUserActions:
    def test_activate_user(self):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )
        assert user.is_activated is False

        user.activate()

        assert user.is_activated is True

    def test_confirm_user(self):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

        assert user.is_confirmed is False

        user.confirm(user.confirmation_token)

        assert user.is_confirmed is True

    def test_confirm_user_with_invalid_token_raises_exception(self):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

        assert user.is_confirmed is False
        with pytest.raises(InvalidConfirmationTokenException):
            user.confirm("invalid_token")

        assert user.is_confirmed is False

    def test_change_password(self):
        old_password = "StrongPassword123!@#"
        new_password = "NewStrongPassword123!@#"
        user = build_new_user(
            email="abc@abc.com",
            password=old_password,
            role=UserRole.USER,
        )

        assert verify_password(old_password, user.hashed_password)

        user.change_password(old_password, new_password)

        assert verify_password(new_password, user.hashed_password)

    def test_change_password_with_weak_password_should_raise_exception(self):
        old_password = "StrongPassword123!@#"
        new_password = "weakpassword"
        user = build_new_user(
            email="abc@abc.com",
            password=old_password,
            role=UserRole.USER,
        )

        assert verify_password(old_password, user.hashed_password)

        with pytest.raises(PasswordNotStrongException):
            user.change_password(old_password, new_password)


class TestUserPlatformRoles:
    def test_user_is_platform_owner(self):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

        organization = Organization(
            name="Platform",
            description="Platform Owner",
            role=OrganizationRole.PLATFORM_OWNER,
        )

        user.organization = organization

        assert user.is_platform_owner() is True
        assert user.is_platform_user() is False

    def test_user_is_platform_user(self):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

        organization = Organization(
            name="Platform",
            description="Platform Owner",
            role=OrganizationRole.PLATFORM_USER,
        )

        user.organization = organization

        assert user.is_platform_user() is True
        assert user.is_platform_owner() is False

    def test_user_without_organization_is_neither_platform_owner_nor_platform_user(
        self,
    ):
        user = build_new_user(
            email="abc@abc.com",
            password="StrongPassword123!@#",
            role=UserRole.USER,
        )

        assert user.is_platform_user() is False
        assert user.is_platform_owner() is False
