"""Add position_id to teachers_local."""

from alembic import op
import sqlalchemy as sa

revision = "20260404_05"
down_revision = "20260403_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teachers_local", sa.Column("position_id", sa.Integer(), nullable=True))
    op.create_index("ix_teachers_local_position_id", "teachers_local", ["position_id"], unique=False)
    op.create_foreign_key(
        "fk_teachers_local_position_id_positions",
        "teachers_local",
        "positions",
        ["position_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_teachers_local_position_id_positions", "teachers_local", type_="foreignkey")
    op.drop_index("ix_teachers_local_position_id", table_name="teachers_local")
    op.drop_column("teachers_local", "position_id")
