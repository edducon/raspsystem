"""Add backend-managed retake tables."""

from alembic import op

revision = "20260403_03"
down_revision = "20260403_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS teachers_local (
            uuid uuid PRIMARY KEY,
            full_name varchar(255) NOT NULL,
            department_ids integer[] NOT NULL DEFAULT '{}'
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_teachers_local_full_name ON teachers_local (full_name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS past_semester (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            group_name varchar(255) NOT NULL,
            subject_name text NOT NULL,
            teacher_names text[] NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_past_semester_group_name ON past_semester (group_name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS retakes (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            group_uuid uuid NOT NULL,
            subject_uuid uuid NOT NULL,
            date varchar(10) NOT NULL,
            time_slots integer[] NOT NULL,
            room_uuid text NULL,
            link text NULL,
            attempt_number integer NOT NULL DEFAULT 1,
            created_by varchar(50) NULL,
            created_at timestamp without time zone NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_retakes_group_uuid ON retakes (group_uuid)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_retakes_subject_uuid ON retakes (subject_uuid)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_retakes_date ON retakes (date)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS retake_teachers (
            retake_id uuid NOT NULL REFERENCES retakes(id) ON DELETE CASCADE,
            teacher_uuid uuid NOT NULL REFERENCES teachers_local(uuid),
            role varchar(32) NOT NULL,
            PRIMARY KEY (retake_id, teacher_uuid)
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS retake_teachers")
    op.execute("DROP INDEX IF EXISTS ix_retakes_date")
    op.execute("DROP INDEX IF EXISTS ix_retakes_subject_uuid")
    op.execute("DROP INDEX IF EXISTS ix_retakes_group_uuid")
    op.execute("DROP TABLE IF EXISTS retakes")
    op.execute("DROP INDEX IF EXISTS ix_past_semester_group_name")
    op.execute("DROP TABLE IF EXISTS past_semester")
    op.execute("DROP INDEX IF EXISTS ix_teachers_local_full_name")
    op.execute("DROP TABLE IF EXISTS teachers_local")
