"""Add an optional comment to answers.

Revision ID: 20261030_add_answers_comment
Revises: 20261009_base
"""

from alembic import op

revision = "20261030_add_answers_comment"
down_revision = "20261009_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fresh databases already have this column from the canonical SQL.
    op.execute("ALTER TABLE answers ADD COLUMN IF NOT EXISTS comment TEXT")


def downgrade() -> None:
    op.drop_column("answers", "comment")
