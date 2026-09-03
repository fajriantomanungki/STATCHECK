"""Create Phase 6 Release Center tables."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260903_0006"
down_revision: Union[str, None] = "20260903_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "releases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kode_rilis", sa.String(30), nullable=False),
        sa.Column("tanggal_rilis", sa.Date(), nullable=False),
        sa.Column("waktu_rilis", sa.Time(), nullable=False),
        sa.Column("tempat", sa.String(250), nullable=False),
        sa.Column("judul_rilis", sa.String(250), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_releases_kode_rilis", "releases", ["kode_rilis"], unique=True)
    op.create_index("ix_releases_tanggal_rilis", "releases", ["tanggal_rilis"])
    op.create_index("ix_releases_status", "releases", ["status"])

    op.create_table(
        "release_brs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brs_id", name="uq_release_brs_brs_id"),
    )
    op.create_index("ix_release_brs_release_id", "release_brs", ["release_id"])
    op.create_index("ix_release_brs_brs_id", "release_brs", ["brs_id"])

    op.create_table(
        "guests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("nama", sa.String(150), nullable=False),
        sa.Column("instansi", sa.String(200), nullable=False),
        sa.Column("jabatan", sa.String(150), nullable=True),
        sa.Column("nomor_hp", sa.String(30), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guests_release_id", "guests", ["release_id"])

    op.create_table(
        "qna",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("guest_id", sa.Uuid(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("ai_answer", sa.Text(), nullable=True),
        sa.Column("supervisor_answer", sa.Text(), nullable=True),
        sa.Column("pjk_answer", sa.Text(), nullable=True),
        sa.Column("final_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qna_release_id", "qna", ["release_id"])
    op.create_index("ix_qna_guest_id", "qna", ["guest_id"])

    op.create_table(
        "minutes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("release_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("generated_file_path", sa.String(500), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_minutes_release_id", "minutes", ["release_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_minutes_release_id", table_name="minutes")
    op.drop_table("minutes")
    op.drop_index("ix_qna_guest_id", table_name="qna")
    op.drop_index("ix_qna_release_id", table_name="qna")
    op.drop_table("qna")
    op.drop_index("ix_guests_release_id", table_name="guests")
    op.drop_table("guests")
    op.drop_index("ix_release_brs_brs_id", table_name="release_brs")
    op.drop_index("ix_release_brs_release_id", table_name="release_brs")
    op.drop_table("release_brs")
    op.drop_index("ix_releases_status", table_name="releases")
    op.drop_index("ix_releases_tanggal_rilis", table_name="releases")
    op.drop_index("ix_releases_kode_rilis", table_name="releases")
    op.drop_table("releases")
