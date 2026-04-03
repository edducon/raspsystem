"""Add JSON content to schedule snapshots."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260403_04"
down_revision = "20260403_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "schedule_snapshots",
        sa.Column(
            "groups",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "schedule_snapshots",
        sa.Column(
            "subjects",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "schedule_snapshots",
        sa.Column(
            "teachers",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "schedule_snapshots",
        sa.Column(
            "schedule_items",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("schedule_snapshots", "schedule_items")
    op.drop_column("schedule_snapshots", "teachers")
    op.drop_column("schedule_snapshots", "subjects")
    op.drop_column("schedule_snapshots", "groups")
