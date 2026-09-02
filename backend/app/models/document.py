import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.brs import BRS
    from app.models.user import User


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("brs_id", "document_type", "version", name="uq_document_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)
    document_type: Mapped[str] = mapped_column(String(40), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    file_path: Mapped[str] = mapped_column(String(500))
    file_extension: Mapped[str] = mapped_column(String(10))
    mime_type: Mapped[str] = mapped_column(String(150))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    extraction_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    extraction_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brs: Mapped["BRS"] = relationship(back_populates="documents")
    uploader: Mapped["User"] = relationship()
    contents: Mapped[list["DocumentContent"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentContent.page_number"
    )


class DocumentContent(Base):
    __tablename__ = "document_contents"
    __table_args__ = (
        UniqueConstraint("document_id", "page_number", name="uq_document_content_page"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page_number: Mapped[int] = mapped_column(Integer)
    section_label: Mapped[str] = mapped_column(String(50))
    text_content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    document: Mapped[Document] = relationship(back_populates="contents")
