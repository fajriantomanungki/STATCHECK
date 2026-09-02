"""Create Phase 2 BRS tables."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_0002"
down_revision: Union[str, None] = "20260902_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "indicators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nama_indikator", sa.String(200), nullable=False),
        sa.Column("kategori", sa.String(100), nullable=False),
        sa.Column("satuan_default", sa.String(100), nullable=False),
        sa.Column("fungsi", sa.String(150), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_indicators_nama_indikator", "indicators", ["nama_indikator"], unique=True)

    op.create_table(
        "brs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kode_brs", sa.String(30), nullable=False),
        sa.Column("nama_brs", sa.String(250), nullable=False),
        sa.Column("waktu_rilis", sa.Date(), nullable=False),
        sa.Column("fungsi_pj", sa.String(150), nullable=False),
        sa.Column("pjk_id", sa.Uuid(), nullable=False),
        sa.Column("supervisor_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["pjk_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["supervisor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brs_kode_brs", "brs", ["kode_brs"], unique=True)
    op.create_index("ix_brs_nama_brs", "brs", ["nama_brs"])
    op.create_index("ix_brs_status", "brs", ["status"])

    op.create_table(
        "brs_team",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brs_id", "user_id", name="uq_brs_team_user"),
    )

    op.create_table(
        "brs_data",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("brs_id", sa.Uuid(), nullable=False),
        sa.Column("indicator_id", sa.Uuid(), nullable=False),
        sa.Column("sub_indikator", sa.String(200), nullable=True),
        sa.Column("periode_data", sa.Date(), nullable=False),
        sa.Column("deskripsi_periode", sa.String(150), nullable=False),
        sa.Column("nilai_data", sa.Numeric(20, 4), nullable=False),
        sa.Column("satuan", sa.String(100), nullable=False),
        sa.Column("analisis", sa.Text(), nullable=True),
        sa.Column("fenomena", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brs_id"], ["brs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["indicator_id"], ["indicators.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_brs_data_brs_id", "brs_data", ["brs_id"])
    op.create_index("ix_brs_data_indicator_id", "brs_data", ["indicator_id"])


def downgrade() -> None:
    op.drop_index("ix_brs_data_indicator_id", table_name="brs_data")
    op.drop_index("ix_brs_data_brs_id", table_name="brs_data")
    op.drop_table("brs_data")
    op.drop_table("brs_team")
    op.drop_index("ix_brs_status", table_name="brs")
    op.drop_index("ix_brs_nama_brs", table_name="brs")
    op.drop_index("ix_brs_kode_brs", table_name="brs")
    op.drop_table("brs")
    op.drop_index("ix_indicators_nama_indikator", table_name="indicators")
    op.drop_table("indicators")
