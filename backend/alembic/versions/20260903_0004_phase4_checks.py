"""Create Phase 4 automatic check and review tables."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0004"
down_revision: Union[str, None] = "20260903_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "check_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("engine_version", sa.String(30), nullable=False),
        sa.Column("total_checks", sa.Integer(), nullable=False),
        sa.Column("passed_checks", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("suggestion_count", sa.Integer(), nullable=False),
        sa.Column("data_consistency_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("cross_document_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("language_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("initiated_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["initiated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_check_runs_brs_id", "check_runs", ["brs_id"])
    op.create_index("ix_check_runs_status", "check_runs", ["status"])

    op.create_table(
        "check_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("brs_data_id", sa.Uuid(), nullable=True),
        sa.Column("check_type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("field_name", sa.String(250), nullable=True),
        sa.Column("expected_value", sa.Text(), nullable=True),
        sa.Column("actual_value", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("context_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["check_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["brs_data_id"], ["brs_data.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("run_id", "brs_id", "document_id", "brs_data_id", "check_type", "severity", "status"):
        op.create_index(f"ix_check_results_{column}", "check_results", [column])

    op.create_table(
        "check_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("check_result_id", sa.Uuid(), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["check_result_id"], ["check_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_check_reviews_check_result_id", "check_reviews", ["check_result_id"])


def downgrade() -> None:
    op.drop_index("ix_check_reviews_check_result_id", table_name="check_reviews")
    op.drop_table("check_reviews")
    for column in reversed(("run_id", "brs_id", "document_id", "brs_data_id", "check_type", "severity", "status")):
        op.drop_index(f"ix_check_results_{column}", table_name="check_results")
    op.drop_table("check_results")
    op.drop_index("ix_check_runs_status", table_name="check_runs")
    op.drop_index("ix_check_runs_brs_id", table_name="check_runs")
    op.drop_table("check_runs")
