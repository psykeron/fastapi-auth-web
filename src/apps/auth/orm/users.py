from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, func

from .metadata import mapper_registry

users_table = Table(
    "users",
    mapper_registry.metadata,
    Column("id", String(100), primary_key=True),
    Column("email", String(255), unique=True, nullable=False),
    Column("first_name", String(255), nullable=False),
    Column("last_name", String(255), nullable=False),
    Column("hashed_password", String(255), nullable=False),
    Column("is_activated", Boolean, unique=False, default=False, nullable=False),
    Column("is_confirmed", Boolean, unique=False, default=False, nullable=False),
    Column("role", String(10), nullable=False),
    Column("confirmation_token", String(255), nullable=False),
    Column(
        "organization_id", String(32), ForeignKey("organizations.id"), nullable=True
    ),
    Column("created_at", DateTime, default=func.now(), nullable=False),
    Column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now(), nullable=False
    ),
)
