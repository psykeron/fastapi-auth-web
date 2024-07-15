from sqlalchemy import Column, DateTime, String, Table, Text, func

from .metadata import mapper_registry

organizations_table = Table(
    "organizations",
    mapper_registry.metadata,
    Column("id", String(32), primary_key=True),
    Column("name", String(255), unique=True, nullable=False),
    Column("role", String(255), nullable=False),
    Column("description", Text, unique=False, default=False, nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "updated_at",
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    ),
)
