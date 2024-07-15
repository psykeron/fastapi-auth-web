from sqlalchemy.orm import relationship

from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import SensitiveUser, User

from .metadata import mapper_registry
from .organizations import organizations_table
from .users import users_table


def start_mappers():
    if mapper_registry.mappers:
        return
    users_mapper = mapper_registry.map_imperatively(User, users_table)
    sensitive_users_mapper = mapper_registry.map_imperatively(
        SensitiveUser, users_table
    )
    mapper_registry.map_imperatively(Organization, organizations_table)

    users_mapper.add_property(
        "organization",
        relationship(
            Organization,
            primaryjoin=users_table.c.organization_id == organizations_table.c.id,
            lazy="selectin",
        ),
    )
    sensitive_users_mapper.add_property(
        "organization",
        relationship(
            Organization,
            primaryjoin=users_table.c.organization_id == organizations_table.c.id,
            lazy="selectin",
            overlaps="organization",
        ),
    )
