"""Add session version counter to users."""

from alembic import op
import sqlalchemy as sa

revision = "20260407_07"
down_revision = "20260404_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("session_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("users", "session_version")
