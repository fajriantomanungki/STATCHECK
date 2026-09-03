import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.brs import UserSummary


class ApprovalNoteRequest(BaseModel):
    note: str | None = Field(default=None, max_length=3000)


class ApprovalEventResponse(BaseModel):
    id: uuid.UUID
    approval_level: str
    action: str
    from_status: str
    to_status: str
    note: str | None
    user: UserSummary
    created_at: datetime


class ApprovalWorkflowResponse(BaseModel):
    brs_id: uuid.UUID
    current_status: str
    latest_check_id: uuid.UUID | None
    latest_score: Decimal | None
    open_findings: int
    error_count: int
    warning_count: int
    suggestion_count: int
    events: list[ApprovalEventResponse]
