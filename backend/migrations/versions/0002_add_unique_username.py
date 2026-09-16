"""add unique username constraint

Revision ID: 0002_add_unique_username
Revises: 0001_create_users
Create Date: 2026-09-15

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_unique_username"
down_revision: str | None = "0001_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_users_pseudonyme",
        "users",
        ["pseudonyme"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_users_pseudonyme",
        "users",
        type_="unique",
    )