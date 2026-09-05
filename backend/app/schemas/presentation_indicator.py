import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PresentationIndicatorUpdate(BaseModel):
    analysis: str | None = Field(default=None, max_length=20000)
    phenomenon: str | None = Field(default=None, max_length=20000)


class PresentationIndicatorResponse(BaseModel):
    id: uuid.UUID
    brs_id: uuid.UUID
    document_id: uuid.UUID
    indicator_name: str
    value_text: str
    numeric_value: Decimal | None
    unit: str | None
    period_label: str | None
    data_type: str
    comparison_basis: str | None
    value_role: str
    metadata_text: str
    page_number: int
    analysis: str | None
    phenomenon: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
