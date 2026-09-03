import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.access import can_view_brs, require_brs_manage, require_brs_view
from app.api.deps import CurrentUser, DbSession
from app.models.brs import BRS, BRSData, BRSTeam
from app.models.indicator import Indicator
from app.models.user import User
from app.schemas.brs import (
    BRSCreate,
    BRSDataCreate,
    BRSDataResponse,
    BRSDetailResponse,
    BRSListResponse,
    BRSUpdate,
)
from app.services.file_storage import resolve_stored_path

router = APIRouter(prefix="/brs", tags=["BRS"])


def brs_query():
    return select(BRS).options(
        selectinload(BRS.pjk),
        selectinload(BRS.supervisor),
        selectinload(BRS.team).selectinload(BRSTeam.user),
        selectinload(BRS.data),
        selectinload(BRS.documents),
    )


def get_brs_or_404(db: DbSession, brs_id: uuid.UUID) -> BRS:
    brs = db.scalar(brs_query().where(BRS.id == brs_id))
    if brs is None:
        raise HTTPException(status_code=404, detail="BRS tidak ditemukan.")
    return brs


def brs_payload(brs: BRS) -> dict:
    return {
        "id": brs.id,
        "kode_brs": brs.kode_brs,
        "nama_brs": brs.nama_brs,
        "waktu_rilis": brs.waktu_rilis,
        "fungsi_pj": brs.fungsi_pj,
        "status": brs.status,
        "pjk": brs.pjk,
        "supervisor": brs.supervisor,
        "team": brs.team,
        "jumlah_data": len(brs.data),
        "jumlah_dokumen": sum(document.status == "active" for document in brs.documents),
        "created_at": brs.created_at,
        "updated_at": brs.updated_at,
    }


def validate_users(db: DbSession, user_ids: list[uuid.UUID]) -> list[User]:
    unique_ids = list(dict.fromkeys(user_ids))
    if not unique_ids:
        return []
    users = list(db.scalars(select(User).where(User.id.in_(unique_ids), User.is_active.is_(True))))
    if len(users) != len(unique_ids):
        raise HTTPException(status_code=422, detail="Terdapat anggota tim yang tidak valid atau tidak aktif.")
    return users


def replace_team(brs: BRS, users: list[User], pjk_id: uuid.UUID) -> None:
    brs.team.clear()
    for user in users:
        if user.id != pjk_id:
            brs.team.append(BRSTeam(user_id=user.id, role="penyusun"))


@router.get("", response_model=list[BRSListResponse])
def list_brs(current_user: CurrentUser, db: DbSession, search: str | None = None) -> list[dict]:
    query = brs_query().order_by(BRS.waktu_rilis.desc(), BRS.created_at.desc())
    if search:
        query = query.where(BRS.nama_brs.ilike(f"%{search.strip()}%"))
    records = list(db.scalars(query).unique())
    return [brs_payload(item) for item in records if can_view_brs(current_user, item)]


@router.post("", response_model=BRSDetailResponse, status_code=status.HTTP_201_CREATED)
def create_brs(payload: BRSCreate, current_user: CurrentUser, db: DbSession) -> dict:
    if current_user.user_level not in {"admin", "pjk"}:
        raise HTTPException(status_code=403, detail="Hanya PJK atau administrator yang dapat mendaftarkan BRS.")
    if payload.supervisor_id == current_user.id:
        raise HTTPException(status_code=422, detail="PJK tidak dapat menjadi supervisor untuk BRS yang sama.")
    related_ids = payload.team_user_ids + ([payload.supervisor_id] if payload.supervisor_id else [])
    users = validate_users(db, related_ids)
    team_users = [user for user in users if user.id in payload.team_user_ids]
    brs_id = uuid.uuid4()
    brs = BRS(
        id=brs_id,
        kode_brs=f"BRS-{payload.waktu_rilis.year}-{brs_id.hex[:6].upper()}",
        nama_brs=payload.nama_brs.strip(),
        waktu_rilis=payload.waktu_rilis,
        fungsi_pj=payload.fungsi_pj.strip(),
        pjk_id=current_user.id,
        supervisor_id=payload.supervisor_id,
        status="draft",
    )
    replace_team(brs, team_users, current_user.id)
    db.add(brs)
    db.commit()
    return brs_payload(get_brs_or_404(db, brs.id))


@router.get("/{brs_id}", response_model=BRSDetailResponse)
def read_brs(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_brs_view(current_user, brs)
    return brs_payload(brs)


@router.put("/{brs_id}", response_model=BRSDetailResponse)
def update_brs(brs_id: uuid.UUID, payload: BRSUpdate, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    if payload.supervisor_id == current_user.id:
        raise HTTPException(status_code=422, detail="PJK tidak dapat menjadi supervisor untuk BRS yang sama.")
    related_ids = payload.team_user_ids + ([payload.supervisor_id] if payload.supervisor_id else [])
    users = validate_users(db, related_ids)
    brs.nama_brs = payload.nama_brs.strip()
    brs.waktu_rilis = payload.waktu_rilis
    brs.fungsi_pj = payload.fungsi_pj.strip()
    brs.supervisor_id = payload.supervisor_id
    replace_team(brs, [user for user in users if user.id in payload.team_user_ids], brs.pjk_id)
    db.commit()
    return brs_payload(get_brs_or_404(db, brs.id))


@router.delete("/{brs_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brs(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    stored_files = [document.file_path for document in brs.documents]
    db.delete(brs)
    db.commit()
    for file_path in stored_files:
        try:
            resolve_stored_path(file_path).unlink(missing_ok=True)
        except (OSError, ValueError):
            # Penghapusan data utama tetap berhasil. File yatim dapat dibersihkan
            # melalui pemeliharaan storage bila filesystem sedang bermasalah.
            continue


@router.get("/{brs_id}/data", response_model=list[BRSDataResponse])
def list_brs_data(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> list[BRSData]:
    brs = get_brs_or_404(db, brs_id)
    require_brs_view(current_user, brs)
    query = (
        select(BRSData)
        .options(selectinload(BRSData.indicator))
        .where(BRSData.brs_id == brs_id)
        .order_by(BRSData.periode_data.desc(), BRSData.created_at)
    )
    return list(db.scalars(query))


@router.post("/{brs_id}/data", response_model=BRSDataResponse, status_code=status.HTTP_201_CREATED)
def create_brs_data(brs_id: uuid.UUID, payload: BRSDataCreate, current_user: CurrentUser, db: DbSession) -> BRSData:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    indicator = db.get(Indicator, payload.indicator_id)
    if indicator is None or not indicator.is_active:
        raise HTTPException(status_code=422, detail="Indikator tidak valid atau tidak aktif.")
    data = BRSData(brs_id=brs.id, created_by=current_user.id, **payload.model_dump())
    db.add(data)
    db.commit()
    return db.scalar(select(BRSData).options(selectinload(BRSData.indicator)).where(BRSData.id == data.id))


@router.put("/{brs_id}/data/{data_id}", response_model=BRSDataResponse)
def update_brs_data(brs_id: uuid.UUID, data_id: uuid.UUID, payload: BRSDataCreate, current_user: CurrentUser, db: DbSession) -> BRSData:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    data = db.scalar(select(BRSData).where(BRSData.id == data_id, BRSData.brs_id == brs_id))
    if data is None:
        raise HTTPException(status_code=404, detail="Data BRS tidak ditemukan.")
    indicator = db.get(Indicator, payload.indicator_id)
    if indicator is None or not indicator.is_active:
        raise HTTPException(status_code=422, detail="Indikator tidak valid atau tidak aktif.")
    for key, value in payload.model_dump().items():
        setattr(data, key, value)
    data.updated_at = datetime.now(data.updated_at.tzinfo)
    db.commit()
    return db.scalar(select(BRSData).options(selectinload(BRSData.indicator)).where(BRSData.id == data.id))


@router.delete("/{brs_id}/data/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brs_data(brs_id: uuid.UUID, data_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    data = db.scalar(select(BRSData).where(BRSData.id == data_id, BRSData.brs_id == brs_id))
    if data is None:
        raise HTTPException(status_code=404, detail="Data BRS tidak ditemukan.")
    db.delete(data)
    db.commit()
