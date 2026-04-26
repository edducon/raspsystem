"""add retake control types

Revision ID: 20260426_12
Revises: 20260425_11
Create Date: 2026-04-26 15:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260426_12"
down_revision = "20260425_11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "retakes",
        sa.Column("control_type", sa.String(length=32), server_default="unspecified", nullable=False),
    )
    op.create_index(op.f("ix_retakes_control_type"), "retakes", ["control_type"], unique=False)

    op.create_table(
        "retake_subject_controls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("group_uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("group_number", sa.String(length=50), nullable=False),
        sa.Column("group_family_key", sa.String(length=50), nullable=True),
        sa.Column("subject_key", sa.String(length=255), nullable=False),
        sa.Column("subject_name", sa.Text(), nullable=False),
        sa.Column("control_type", sa.String(length=32), server_default="unspecified", nullable=False),
        sa.Column("updated_by", sa.String(length=50), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_uuid", "subject_key", name="uq_retake_subject_controls_group_subject"),
    )
    op.create_index(op.f("ix_retake_subject_controls_control_type"), "retake_subject_controls", ["control_type"], unique=False)
    op.create_index(op.f("ix_retake_subject_controls_group_family_key"), "retake_subject_controls", ["group_family_key"], unique=False)
    op.create_index(op.f("ix_retake_subject_controls_group_number"), "retake_subject_controls", ["group_number"], unique=False)
    op.create_index(op.f("ix_retake_subject_controls_group_uuid"), "retake_subject_controls", ["group_uuid"], unique=False)
    op.create_index(op.f("ix_retake_subject_controls_subject_key"), "retake_subject_controls", ["subject_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_retake_subject_controls_subject_key"), table_name="retake_subject_controls")
    op.drop_index(op.f("ix_retake_subject_controls_group_uuid"), table_name="retake_subject_controls")
    op.drop_index(op.f("ix_retake_subject_controls_group_number"), table_name="retake_subject_controls")
    op.drop_index(op.f("ix_retake_subject_controls_group_family_key"), table_name="retake_subject_controls")
    op.drop_index(op.f("ix_retake_subject_controls_control_type"), table_name="retake_subject_controls")
    op.drop_table("retake_subject_controls")

    op.drop_index(op.f("ix_retakes_control_type"), table_name="retakes")
    op.drop_column("retakes", "control_type")
