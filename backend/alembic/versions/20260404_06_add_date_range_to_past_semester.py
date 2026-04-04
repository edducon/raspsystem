"""Add date range metadata to past_semester."""

from alembic import op
import sqlalchemy as sa

revision = "20260404_06"
down_revision = "20260404_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("past_semester", sa.Column("date_range_start", sa.String(length=10), nullable=True))
    op.add_column("past_semester", sa.Column("date_range_end", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("past_semester", "date_range_end")
    op.drop_column("past_semester", "date_range_start")
