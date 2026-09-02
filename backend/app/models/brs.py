import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.indicator import Indicator
    from app.models.user import User


class BRS(Base):
    __tablename__ = "brs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kode_brs: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    nama_brs: Mapped[str] = mapped_column(String(250), index=True)
    waktu_rilis: Mapped[date] = mapped_column(Date)
    fungsi_pj: Mapped[str] = mapped_column(String(150))
    pjk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    pjk: Mapped["User"] = relationship(foreign_keys=[pjk_id])
    supervisor: Mapped["User | None"] = relationship(foreign_keys=[supervisor_id])
    team: Mapped[list["BRSTeam"]] = relationship(back_populates="brs", cascade="all, delete-orphan")
    data: Mapped[list["BRSData"]] = relationship(back_populates="brs", cascade="all, delete-orphan")


class BRSTeam(Base):
    __tablename__ = "brs_team"
    __table_args__ = (UniqueConstraint("brs_id", "user_id", name="uq_brs_team_user"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(50), default="penyusun")

    brs: Mapped[BRS] = relationship(back_populates="team")
    user: Mapped["User"] = relationship()


class BRSData(Base):
    __tablename__ = "brs_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)
    indicator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("indicators.id"), index=True)
    sub_indikator: Mapped[str | None] = mapped_column(String(200), nullable=True)
    periode_data: Mapped[date] = mapped_column(Date)
    deskripsi_periode: Mapped[str] = mapped_column(String(150))
    nilai_data: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    satuan: Mapped[str] = mapped_column(String(100))
    analisis: Mapped[str | None] = mapped_column(Text, nullable=True)
    fenomena: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brs: Mapped[BRS] = relationship(back_populates="data")
    indicator: Mapped["Indicator"] = relationship(back_populates="brs_data")
    creator: Mapped["User"] = relationship()
