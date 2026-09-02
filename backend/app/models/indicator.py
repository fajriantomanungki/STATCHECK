import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.brs import BRSData


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nama_indikator: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    kategori: Mapped[str] = mapped_column(String(100))
    satuan_default: Mapped[str] = mapped_column(String(100))
    fungsi: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brs_data: Mapped[list["BRSData"]] = relationship(back_populates="indicator")
