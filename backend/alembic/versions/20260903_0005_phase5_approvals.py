"""Create Phase 5 approval audit table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0005"
down_revision: Union[str, None] = "20260903_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("approval_level", sa.String(30), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("from_status", sa.String(40), nullable=False),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("brs_id", "user_id", "approval_level", "action"):
        op.create_index(f"ix_approvals_{column}", "approvals", [column])


def downgrade() -> None:
    for column in reversed(("brs_id", "user_id", "approval_level", "action")):
        op.drop_index(f"ix_approvals_{column}", table_name="approvals")
    op.drop_table("approvals")
