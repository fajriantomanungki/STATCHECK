import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.brs import BRS
    from app.models.user import User


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    kode_rilis: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    tanggal_rilis: Mapped[date] = mapped_column(Date, index=True)
    waktu_rilis: Mapped[time] = mapped_column(Time)
    tempat: Mapped[str] = mapped_column(String(250))
    judul_rilis: Mapped[str] = mapped_column(String(250))
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    creator: Mapped["User"] = relationship()
    brs_links: Mapped[list["ReleaseBRS"]] = relationship(back_populates="release", cascade="all, delete-orphan")
    guests: Mapped[list["Guest"]] = relationship(back_populates="release", cascade="all, delete-orphan")
    qna_items: Mapped[list["QnA"]] = relationship(back_populates="release", cascade="all, delete-orphan")
    minutes: Mapped["ReleaseMinutes | None"] = relationship(back_populates="release", cascade="all, delete-orphan")


class ReleaseBRS(Base):
    __tablename__ = "release_brs"
    __table_args__ = (UniqueConstraint("brs_id", name="uq_release_brs_brs_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)

    release: Mapped[Release] = relationship(back_populates="brs_links")
    brs: Mapped["BRS"] = relationship(back_populates="release_link")


class Guest(Base):
    __tablename__ = "guests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True)
    nama: Mapped[str] = mapped_column(String(150))
    instansi: Mapped[str] = mapped_column(String(200))
    jabatan: Mapped[str | None] = mapped_column(String(150), nullable=True)
    nomor_hp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    release: Mapped[Release] = relationship(back_populates="guests")
    qna_items: Mapped[list["QnA"]] = relationship(back_populates="guest")


class QnA(Base):
    __tablename__ = "qna"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), index=True)
    guest_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("guests.id", ondelete="SET NULL"), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text)
    ai_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    supervisor_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    pjk_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    release: Mapped[Release] = relationship(back_populates="qna_items")
    guest: Mapped[Guest | None] = relationship(back_populates="qna_items")


class ReleaseMinutes(Base):
    __tablename__ = "minutes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("releases.id", ondelete="CASCADE"), unique=True, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    release: Mapped[Release] = relationship(back_populates="minutes")
    creator: Mapped["User"] = relationship()

