"""Create users table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nama", sa.String(length=150), nullable=False),
        sa.Column("nik", sa.String(length=50), nullable=False),
        sa.Column("user_level", sa.String(length=30), nullable=False),
        sa.Column("fungsi", sa.String(length=150), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_nik", "users", ["nik"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_nik", table_name="users")
    op.drop_table("users")
