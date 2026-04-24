"""Add shared retake meetings and department snapshot."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260424_10"
down_revision = "20260407_09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "retake_meetings",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("date", sa.String(length=10), nullable=False),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )
    op.create_index("ix_retake_meetings_department_id", "retake_meetings", ["department_id"], unique=False)
    op.create_index("ix_retake_meetings_date", "retake_meetings", ["date"], unique=False)
    op.add_column("retakes", sa.Column("meeting_id", postgresql.UUID(as_uuid=False), nullable=True))
    op.add_column("retakes", sa.Column("department_id", sa.Integer(), nullable=True))
    op.create_index("ix_retakes_meeting_id", "retakes", ["meeting_id"], unique=False)
    op.create_index("ix_retakes_department_id", "retakes", ["department_id"], unique=False)
    op.create_foreign_key("fk_retakes_meeting_id_retake_meetings", "retakes", "retake_meetings", ["meeting_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_retakes_department_id_departments", "retakes", "departments", ["department_id"], ["id"])
    op.create_table(
        "retake_lead_teachers",
        sa.Column("retake_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("teacher_uuid", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["retake_id"], ["retakes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_uuid"], ["teachers_local.uuid"]),
        sa.PrimaryKeyConstraint("retake_id", "teacher_uuid"),
    )
    op.execute(
        """
        INSERT INTO retake_lead_teachers (retake_id, teacher_uuid)
        SELECT retake_id, teacher_uuid FROM retake_teachers WHERE role = 'MAIN'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("retake_lead_teachers")
    op.drop_constraint("fk_retakes_department_id_departments", "retakes", type_="foreignkey")
    op.drop_constraint("fk_retakes_meeting_id_retake_meetings", "retakes", type_="foreignkey")
    op.drop_index("ix_retakes_department_id", table_name="retakes")
    op.drop_index("ix_retakes_meeting_id", table_name="retakes")
    op.drop_column("retakes", "department_id")
    op.drop_column("retakes", "meeting_id")
    op.drop_index("ix_retake_meetings_date", table_name="retake_meetings")
    op.drop_index("ix_retake_meetings_department_id", table_name="retake_meetings")
    op.drop_table("retake_meetings")
