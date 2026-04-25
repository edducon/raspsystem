"""Add shared retake meetings and department snapshot."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260424_10"
down_revision = "20260420_10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS retake_meetings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            department_id integer NULL REFERENCES departments(id),
            date varchar(10) NOT NULL,
            link text NULL,
            title varchar(255) NULL,
            created_by varchar(50) NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_retake_meetings_department_id ON retake_meetings (department_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_retake_meetings_date ON retake_meetings (date)")
    op.execute("ALTER TABLE retakes ADD COLUMN IF NOT EXISTS meeting_id uuid NULL")
    op.execute("ALTER TABLE retakes ADD COLUMN IF NOT EXISTS department_id integer NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_retakes_meeting_id ON retakes (meeting_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_retakes_department_id ON retakes (department_id)")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_retakes_meeting_id_retake_meetings'
            ) THEN
                ALTER TABLE retakes
                ADD CONSTRAINT fk_retakes_meeting_id_retake_meetings
                FOREIGN KEY (meeting_id) REFERENCES retake_meetings(id) ON DELETE SET NULL;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_retakes_department_id_departments'
            ) THEN
                ALTER TABLE retakes
                ADD CONSTRAINT fk_retakes_department_id_departments
                FOREIGN KEY (department_id) REFERENCES departments(id);
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS retake_lead_teachers (
            retake_id uuid NOT NULL REFERENCES retakes(id) ON DELETE CASCADE,
            teacher_uuid uuid NOT NULL REFERENCES teachers_local(uuid),
            PRIMARY KEY (retake_id, teacher_uuid)
        )
        """
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
