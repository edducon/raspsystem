"""Add schedule snapshots."""

from alembic import op
import sqlalchemy as sa

revision = "20260403_02"
down_revision = "20260403_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("semester_label", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="raspyx"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_reference_for_retakes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_schedule_snapshots_name", "schedule_snapshots", ["name"], unique=False)
    op.create_index("ix_schedule_snapshots_semester_label", "schedule_snapshots", ["semester_label"], unique=False)
    op.create_index("ix_schedule_snapshots_status", "schedule_snapshots", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_schedule_snapshots_status", table_name="schedule_snapshots")
    op.drop_index("ix_schedule_snapshots_semester_label", table_name="schedule_snapshots")
    op.drop_index("ix_schedule_snapshots_name", table_name="schedule_snapshots")
    op.drop_table("schedule_snapshots")
