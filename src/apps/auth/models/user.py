import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from src.lib_auth.password import (
    InvalidPasswordException,
    hash_password,
    verify_password,
)
from src.lib_auth.roles import OrganizationRole, UserRole

from .organization import Organization


class PasswordNotStrongException(Exception):
    pass


class AuthenticationException(Exception):
    pass


class InvalidEmailException(Exception):
    pass


class InvalidConfirmationTokenException(Exception):
    pass


class PasswordStrengthChecker(Protocol):
    @staticmethod
    def check(password: str) -> bool: ...

    @staticmethod
    def get_instructions() -> str: ...


class NaivePasswordStrengthChecker:
    @staticmethod
    def check(password: str) -> bool:
        return bool(
            password
            and len(password) >= 16
            and re.search(r"[0-9]", password)
            and re.search(r"[^0-9a-zA-Z]", password)
        )

    @staticmethod
    def get_instructions() -> str:
        return "Password should contain at least 16 characters, 1 digit, and 1 symbol."


@dataclass
class User:
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_activated: bool = False  # this flag indicates that we activated the account
    is_confirmed: bool = (
        False  # this flag indicates that the user confirmed the account
    )
    role: UserRole = UserRole.USER

    organization: Organization | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def activate(self):
        self.is_activated = True

    def deactivate(self):
        self.is_activated = False

    def is_platform_owner(self) -> bool:
        return (
            self.organization is not None
            and self.organization.role == OrganizationRole.PLATFORM_OWNER
        )

    def is_platform_user(self) -> bool:
        return (
            self.organization is not None
            and self.organization.role == OrganizationRole.PLATFORM_USER
        )


@dataclass
class SensitiveUser(User):
    hashed_password: str | None = None
    confirmation_token: str | None = None

    def change_password(
        self,
        old_password: str,
        new_password: str,
        skip_check: bool = False,
        password_strength_checker: (
            PasswordStrengthChecker | None
        ) = NaivePasswordStrengthChecker,
    ):
        if not skip_check:
            if not verify_password(old_password, self.hashed_password):
                raise AuthenticationException("Old password is not valid")

        if password_strength_checker and not password_strength_checker.check(
            new_password
        ):
            raise PasswordNotStrongException(
                password_strength_checker.get_instructions()
            )

        self.hashed_password = hash_password(new_password)

    def confirm(self, confirmation_token: str | None):
        if not confirmation_token or confirmation_token != self.confirmation_token:
            raise InvalidConfirmationTokenException("Confirmation token is not valid")
        self.is_confirmed = True

    def authenticate(self, password: str) -> bool:
        if not self.is_activated:
            raise AuthenticationException("User is not activated")

        if not self.is_confirmed:
            raise AuthenticationException("User is not confirmed")

        try:
            verify_password(password, self.hashed_password)
        except InvalidPasswordException:
            raise AuthenticationException("Password is not valid")

        return True


def build_new_user(
    email: str,
    password: str,
    role: UserRole,
    first_name: str | None = None,
    last_name: str | None = None,
    password_strength_checker: (
        PasswordStrengthChecker | None
    ) = NaivePasswordStrengthChecker,
) -> SensitiveUser:
    if not email:
        raise InvalidEmailException("Email is invalid")

    if password_strength_checker and not password_strength_checker.check(password):
        raise PasswordNotStrongException(password_strength_checker.get_instructions())

    hashed_password = hash_password(password)

    return SensitiveUser(
        id=uuid4().hex,
        email=email,
        hashed_password=hashed_password,
        is_activated=False,
        is_confirmed=False,
        confirmation_token=uuid4().hex,
        role=role,
        first_name=first_name,
        last_name=last_name,
    )
