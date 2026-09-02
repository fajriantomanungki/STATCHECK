"""Create Phase 3 document tables."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0003"
down_revision: Union[str, None] = "20260902_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(40), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_extension", sa.String(10), nullable=False),
        sa.Column("mime_type", sa.String(150), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("extraction_status", sa.String(30), nullable=False),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brs_id", "document_type", "version", name="uq_document_version"),
        sa.UniqueConstraint("stored_name"),
    )
    op.create_index("ix_documents_brs_id", "documents", ["brs_id"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_extraction_status", "documents", ["extraction_status"])

    op.create_table(
        "document_contents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("section_label", sa.String(50), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "page_number", name="uq_document_content_page"),
    )
    op.create_index("ix_document_contents_document_id", "document_contents", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_contents_document_id", table_name="document_contents")
    op.drop_table("document_contents")
    op.drop_index("ix_documents_extraction_status", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_index("ix_documents_brs_id", table_name="documents")
    op.drop_table("documents")
