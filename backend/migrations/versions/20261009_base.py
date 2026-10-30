"""Baseline for the canonical SQL-initialized schema.

The location revisions are intentionally excluded. Schema creation remains
owned by database/init/01-postgis.sql.
"""

revision = "20261009_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
