"""Initial reference tables for departments, positions, teachers, and users."""

from alembic import op
import sqlalchemy as sa

revision = "20260403_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("short_name", sa.String(length=100), nullable=False),
    )
    op.create_index("ix_departments_name", "departments", ["name"], unique=True)
    op.create_index("ix_departments_short_name", "departments", ["short_name"], unique=True)

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_positions_name", "positions", ["name"], unique=True)

    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("position_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["position_id"], ["positions.id"]),
    )
    op.create_index("ix_teachers_full_name", "teachers", ["full_name"], unique=False)
    op.create_index("ix_teachers_department_id", "teachers", ["department_id"], unique=False)
    op.create_index("ix_teachers_position_id", "teachers", ["position_id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("department_ids", sa.ARRAY(sa.Integer()), nullable=False, server_default="{}"),
        sa.Column("teacher_uuid", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_role", "users", ["role"], unique=False)
    op.create_index("ix_users_teacher_uuid", "users", ["teacher_uuid"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_teacher_uuid", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_teachers_position_id", table_name="teachers")
    op.drop_index("ix_teachers_department_id", table_name="teachers")
    op.drop_index("ix_teachers_full_name", table_name="teachers")
    op.drop_table("teachers")

    op.drop_index("ix_positions_name", table_name="positions")
    op.drop_table("positions")

    op.drop_index("ix_departments_short_name", table_name="departments")
    op.drop_index("ix_departments_name", table_name="departments")
    op.drop_table("departments")
