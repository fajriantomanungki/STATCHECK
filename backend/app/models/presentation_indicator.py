import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.brs import BRS
    from app.models.document import Document
    from app.models.user import User


class PresentationIndicator(Base):
    """Angka indikator dari Bahan Paparan dan Narasi Pimpinan aktif."""

    __tablename__ = "presentation_indicators"
    __table_args__ = (
        UniqueConstraint("document_id", "source_hash", name="uq_presentation_indicator_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    indicator_name: Mapped[str] = mapped_column(String(250), index=True)
    value_text: Mapped[str] = mapped_column(String(100))
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    period_label: Mapped[str | None] = mapped_column(String(150), nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), default="number")
    comparison_basis: Mapped[str | None] = mapped_column(String(50), nullable=True)
    value_role: Mapped[str] = mapped_column(String(30), default="level")
    metadata_text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int] = mapped_column(Integer)
    source_hash: Mapped[str] = mapped_column(String(64))
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    phenomenon: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brs: Mapped["BRS"] = relationship(back_populates="presentation_indicators")
    document: Mapped["Document"] = relationship()
    creator: Mapped["User"] = relationship()

    @property
    def source_document_type(self) -> str:
        return self.document.document_type

    @property
    def source_document_name(self) -> str:
        return self.document.file_name
