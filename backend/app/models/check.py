import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.user import utc_now

if TYPE_CHECKING:
    from app.models.brs import BRS, BRSData
    from app.models.document import Document
    from app.models.user import User


class CheckRun(Base):
    __tablename__ = "check_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed", index=True)
    engine_version: Mapped[str] = mapped_column(String(30), default="rules-v1")
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    passed_checks: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    suggestion_count: Mapped[int] = mapped_column(Integer, default=0)
    data_consistency_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    cross_document_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    language_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    initiated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    brs: Mapped["BRS"] = relationship(back_populates="check_runs")
    initiator: Mapped["User"] = relationship()
    results: Mapped[list["CheckResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="CheckResult.created_at"
    )


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("check_runs.id", ondelete="CASCADE"), index=True
    )
    brs_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brs.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    brs_data_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brs_data.id", ondelete="SET NULL"), nullable=True, index=True
    )
    check_type: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    field_name: Mapped[str | None] = mapped_column(String(250), nullable=True)
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    context_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    run: Mapped[CheckRun] = relationship(back_populates="results")
    document: Mapped["Document | None"] = relationship()
    brs_data: Mapped["BRSData | None"] = relationship()
    reviews: Mapped[list["CheckReview"]] = relationship(
        back_populates="result", cascade="all, delete-orphan", order_by="CheckReview.created_at"
    )


class CheckReview(Base):
    __tablename__ = "check_reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    check_result_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("check_results.id", ondelete="CASCADE"), index=True
    )
    reviewed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(40))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    result: Mapped[CheckResult] = relationship(back_populates="reviews")
    reviewer: Mapped["User"] = relationship()
