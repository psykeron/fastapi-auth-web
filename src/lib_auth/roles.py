from enum import StrEnum


class OrganizationRole(StrEnum):
    PLATFORM_USER = "platform_user"
    PLATFORM_OWNER = "platform_owner"


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"
