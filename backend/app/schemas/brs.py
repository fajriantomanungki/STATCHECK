import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.indicator import IndicatorResponse


class UserSummary(BaseModel):
    id: uuid.UUID
    nama: str
    nik: str
    user_level: str
    fungsi: str | None

    model_config = ConfigDict(from_attributes=True)


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    role: str
    user: UserSummary

    model_config = ConfigDict(from_attributes=True)


class BRSCreate(BaseModel):
    nama_brs: str = Field(min_length=3, max_length=250)
    waktu_rilis: date
    fungsi_pj: str = Field(min_length=2, max_length=150)
    supervisor_id: uuid.UUID | None = None
    team_user_ids: list[uuid.UUID] = Field(default_factory=list)


class BRSUpdate(BRSCreate):
    pass


class BRSListResponse(BaseModel):
    id: uuid.UUID
    kode_brs: str
    nama_brs: str
    waktu_rilis: date
    fungsi_pj: str
    status: str
    pjk: UserSummary
    supervisor: UserSummary | None
    jumlah_data: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BRSDetailResponse(BRSListResponse):
    team: list[TeamMemberResponse]
    updated_at: datetime


class BRSDataCreate(BaseModel):
    indicator_id: uuid.UUID
    sub_indikator: str | None = Field(default=None, max_length=200)
    periode_data: date
    deskripsi_periode: str = Field(min_length=2, max_length=150)
    nilai_data: Decimal
    satuan: str = Field(min_length=1, max_length=100)
    analisis: str | None = None
    fenomena: str | None = None


class BRSDataUpdate(BRSDataCreate):
    pass


class BRSDataResponse(BRSDataCreate):
    id: uuid.UUID
    brs_id: uuid.UUID
    indicator: IndicatorResponse
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    total_brs: int
    draft_brs: int
    total_indicators: int
    total_brs_data: int
