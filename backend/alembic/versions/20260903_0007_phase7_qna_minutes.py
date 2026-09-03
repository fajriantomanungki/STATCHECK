"""Extend Q&A and minutes for Phase 7."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0007"
down_revision: Union[str, None] = "20260903_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("qna") as batch_op:
        batch_op.add_column(sa.Column("ai_model", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("ai_sources", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("finalized_by", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key("fk_qna_finalized_by_users", "users", ["finalized_by"], ["id"])
        batch_op.create_index("ix_qna_finalized_by", ["finalized_by"])

    with op.batch_alter_table("minutes") as batch_op:
        batch_op.add_column(sa.Column("opening", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("discussion", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("conclusion", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("docx_file_path", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("pdf_file_path", sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("minutes") as batch_op:
        batch_op.drop_column("pdf_file_path")
        batch_op.drop_column("docx_file_path")
        batch_op.drop_column("conclusion")
        batch_op.drop_column("notes")
        batch_op.drop_column("discussion")
        batch_op.drop_column("opening")

    with op.batch_alter_table("qna") as batch_op:
        batch_op.drop_index("ix_qna_finalized_by")
        batch_op.drop_constraint("fk_qna_finalized_by_users", type_="foreignkey")
        batch_op.drop_column("finalized_at")
        batch_op.drop_column("finalized_by")
        batch_op.drop_column("generated_at")
        batch_op.drop_column("ai_sources")
        batch_op.drop_column("ai_model")
