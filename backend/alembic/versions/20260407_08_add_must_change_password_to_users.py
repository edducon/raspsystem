"""Add must_change_password flag to users."""

from alembic import op
import sqlalchemy as sa

revision = "20260407_08"
down_revision = "20260407_07"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
