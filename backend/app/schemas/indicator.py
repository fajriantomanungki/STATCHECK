import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IndicatorCreate(BaseModel):
    nama_indikator: str = Field(min_length=2, max_length=200)
    kategori: str = Field(min_length=2, max_length=100)
    satuan_default: str = Field(min_length=1, max_length=100)
    fungsi: str | None = Field(default=None, max_length=150)


class IndicatorUpdate(IndicatorCreate):
    is_active: bool = True


class IndicatorResponse(IndicatorUpdate):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
