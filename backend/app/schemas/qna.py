import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.brs import UserSummary
from app.schemas.release import GuestResponse


class QnACreate(BaseModel):
    guest_id: uuid.UUID | None = None
    question: str = Field(min_length=3, max_length=5000)


class QnAAnswersUpdate(BaseModel):
    supervisor_answer: str | None = Field(default=None, max_length=10000)
    pjk_answer: str | None = Field(default=None, max_length=10000)


class QnAFinalize(BaseModel):
    final_answer: str = Field(min_length=2, max_length=10000)


class QnAResponse(BaseModel):
    id: uuid.UUID
    release_id: uuid.UUID
    guest: GuestResponse | None
    question: str
    ai_answer: str | None
    supervisor_answer: str | None
    pjk_answer: str | None
    final_answer: str | None
    ai_model: str | None
    ai_sources: list[str]
    generated_at: datetime | None
    finalizer: UserSummary | None
    finalized_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AIStatusResponse(BaseModel):
    enabled: bool
    model: str


class MinutesUpdate(BaseModel):
    opening: str | None = Field(default=None, max_length=20000)
    discussion: str | None = Field(default=None, max_length=30000)
    notes: str | None = Field(default=None, max_length=20000)
    conclusion: str | None = Field(default=None, max_length=20000)


class MinutesResponse(MinutesUpdate):
    id: uuid.UUID
    release_id: uuid.UUID
    content: str | None
    docx_ready: bool
    pdf_ready: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
