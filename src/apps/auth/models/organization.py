from dataclasses import dataclass
from datetime import datetime

from src.lib_auth.roles import OrganizationRole


@dataclass
class Organization:
    name: str
    description: str
    role: OrganizationRole = OrganizationRole.PLATFORM_USER

    id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
