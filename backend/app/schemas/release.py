import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.schemas.brs import UserSummary


class ReleaseCreate(BaseModel):
    tanggal_rilis: date
    waktu_rilis: time
    tempat: str = Field(min_length=2, max_length=250)
    judul_rilis: str = Field(min_length=3, max_length=250)
    brs_ids: list[uuid.UUID] = Field(min_length=1)


class ReleaseUpdate(BaseModel):
    tanggal_rilis: date
    waktu_rilis: time
    tempat: str = Field(min_length=2, max_length=250)
    judul_rilis: str = Field(min_length=3, max_length=250)


class ReleaseBRSAdd(BaseModel):
    brs_id: uuid.UUID


class ReleaseBRSSummary(BaseModel):
    id: uuid.UUID
    kode_brs: str
    nama_brs: str
    waktu_rilis: date
    fungsi_pj: str
    status: str


class GuestCreate(BaseModel):
    nama: str = Field(min_length=2, max_length=150)
    instansi: str = Field(min_length=2, max_length=200)
    jabatan: str | None = Field(default=None, max_length=150)
    nomor_hp: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=200)


class GuestResponse(GuestCreate):
    id: uuid.UUID
    release_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ReleaseListResponse(BaseModel):
    id: uuid.UUID
    kode_rilis: str
    tanggal_rilis: date
    waktu_rilis: time
    tempat: str
    judul_rilis: str
    status: str
    creator: UserSummary
    jumlah_brs: int
    jumlah_tamu: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReleaseDetailResponse(ReleaseListResponse):
    brs: list[ReleaseBRSSummary]
    guests: list[GuestResponse]

