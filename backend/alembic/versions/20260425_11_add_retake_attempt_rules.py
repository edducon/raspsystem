"""Add global retake attempt rules."""

from alembic import op
import sqlalchemy as sa

revision = "20260425_11"
down_revision = "20260424_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "retake_attempt_rules",
        sa.Column("attempt_number", sa.Integer(), primary_key=True),
        sa.Column("requires_chairman", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("min_commission_members", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.execute(
        """
        INSERT INTO retake_attempt_rules (attempt_number, requires_chairman, min_commission_members)
        VALUES
            (1, false, 1),
            (2, true, 0),
            (3, true, 0)
        ON CONFLICT (attempt_number) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("retake_attempt_rules")
