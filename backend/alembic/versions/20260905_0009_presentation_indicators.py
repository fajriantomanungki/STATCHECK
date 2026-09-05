"""Store indicator rows extracted from presentation documents."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_0009"
down_revision: Union[str, None] = "20260904_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "presentation_indicators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("indicator_name", sa.String(length=250), nullable=False),
        sa.Column("value_text", sa.String(length=100), nullable=False),
        sa.Column("numeric_value", sa.Numeric(20, 4), nullable=True),
        sa.Column("unit", sa.String(length=100), nullable=True),
        sa.Column("period_label", sa.String(length=150), nullable=True),
        sa.Column("data_type", sa.String(length=50), nullable=False),
        sa.Column("comparison_basis", sa.String(length=50), nullable=True),
        sa.Column("value_role", sa.String(length=30), nullable=False),
        sa.Column("metadata_text", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column("phenomenon", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "source_hash", name="uq_presentation_indicator_source"),
    )
    op.create_index("ix_presentation_indicators_brs_id", "presentation_indicators", ["brs_id"])
    op.create_index("ix_presentation_indicators_document_id", "presentation_indicators", ["document_id"])
    op.create_index("ix_presentation_indicators_indicator_name", "presentation_indicators", ["indicator_name"])


def downgrade() -> None:
    op.drop_index("ix_presentation_indicators_indicator_name", table_name="presentation_indicators")
    op.drop_index("ix_presentation_indicators_document_id", table_name="presentation_indicators")
    op.drop_index("ix_presentation_indicators_brs_id", table_name="presentation_indicators")
    op.drop_table("presentation_indicators")
