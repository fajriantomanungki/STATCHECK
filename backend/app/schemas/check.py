import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.brs import UserSummary


class CheckReviewCreate(BaseModel):
    action: Literal["fixed", "confirmed_correct", "ignored"]
    note: str | None = Field(default=None, max_length=2000)


class CheckReviewResponse(BaseModel):
    id: uuid.UUID
    action: str
    note: str | None
    reviewer: UserSummary
    created_at: datetime


class CheckResultResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    document_id: uuid.UUID | None
    document_type: str | None
    document_name: str | None
    brs_data_id: uuid.UUID | None
    check_type: str
    severity: str
    field_name: str | None
    expected_value: str | None
    actual_value: str | None
    message: str
    suggestion: str | None
    status: str
    page_number: int | None
    context_text: str | None
    comparison_values: dict[str, dict[str, str | int | None]] | None
    reviews: list[CheckReviewResponse]
    created_at: datetime
    updated_at: datetime


class CheckRunResponse(BaseModel):
    id: uuid.UUID
    brs_id: uuid.UUID
    status: str
    engine_version: str
    total_checks: int
    passed_checks: int
    error_count: int
    warning_count: int
    suggestion_count: int
    data_consistency_score: Decimal
    cross_document_score: Decimal
    language_score: Decimal
    overall_score: Decimal
    initiator: UserSummary
    started_at: datetime
    completed_at: datetime | None


class CheckRunDetailResponse(CheckRunResponse):
    results: list[CheckResultResponse]
