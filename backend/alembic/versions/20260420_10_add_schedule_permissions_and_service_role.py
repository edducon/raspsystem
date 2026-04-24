"""Add schedule permission flags to users and support SERVICE role."""

from alembic import op
import sqlalchemy as sa

revision = "20260420_10"
down_revision = "20260407_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("can_schedule_semester", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("can_schedule_session", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("can_schedule_retakes", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.alter_column("users", "can_schedule_semester", server_default=None)
    op.alter_column("users", "can_schedule_session", server_default=None)
    op.alter_column("users", "can_schedule_retakes", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "can_schedule_retakes")
    op.drop_column("users", "can_schedule_session")
    op.drop_column("users", "can_schedule_semester")
