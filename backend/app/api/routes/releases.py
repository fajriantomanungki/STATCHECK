import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.brs import BRS
from app.models.release import Guest, Release, ReleaseBRS
from app.models.user import utc_now
from app.schemas.release import (
    GuestCreate,
    GuestResponse,
    ReleaseBRSAdd,
    ReleaseBRSSummary,
    ReleaseCreate,
    ReleaseDetailResponse,
    ReleaseListResponse,
    ReleaseUpdate,
)

router = APIRouter(prefix="/releases", tags=["Release Center"])


def require_release_manager(user: object) -> None:
    if getattr(user, "user_level", None) not in {"admin", "humas"}:
        raise HTTPException(status_code=403, detail="Hanya Humas atau administrator yang dapat mengelola kegiatan rilis.")


def release_query():
    return select(Release).options(
        selectinload(Release.creator),
        selectinload(Release.brs_links).selectinload(ReleaseBRS.brs),
        selectinload(Release.guests),
    )


def get_release_or_404(db: DbSession, release_id: uuid.UUID) -> Release:
    release = db.scalar(release_query().where(Release.id == release_id))
    if release is None:
        raise HTTPException(status_code=404, detail="Kegiatan rilis tidak ditemukan.")
    return release


def release_payload(release: Release, detail: bool = False) -> dict:
    payload = {
        "id": release.id, "kode_rilis": release.kode_rilis,
        "tanggal_rilis": release.tanggal_rilis, "waktu_rilis": release.waktu_rilis,
        "tempat": release.tempat, "judul_rilis": release.judul_rilis,
        "status": release.status, "creator": release.creator,
        "jumlah_brs": len(release.brs_links), "jumlah_tamu": len(release.guests),
        "started_at": release.started_at, "completed_at": release.completed_at,
        "created_at": release.created_at, "updated_at": release.updated_at,
    }
    if detail:
        payload["brs"] = sorted((link.brs for link in release.brs_links), key=lambda item: item.nama_brs)
        payload["guests"] = sorted(release.guests, key=lambda item: item.nama)
    return payload


def validate_brs(db: DbSession, brs_ids: list[uuid.UUID], release_date: date) -> list[BRS]:
    unique_ids = list(dict.fromkeys(brs_ids))
    records = list(db.scalars(
        select(BRS).options(selectinload(BRS.release_link)).where(BRS.id.in_(unique_ids))
    ))
    if len(records) != len(unique_ids):
        raise HTTPException(status_code=422, detail="Terdapat BRS yang tidak ditemukan.")
    invalid_status = [item.nama_brs for item in records if item.status != "release_ready"]
    if invalid_status:
        raise HTTPException(status_code=409, detail="Hanya BRS berstatus Siap Rilis yang dapat dipilih.")
    invalid_date = [item.nama_brs for item in records if item.waktu_rilis != release_date]
    if invalid_date:
        raise HTTPException(status_code=409, detail="Tanggal kegiatan rilis harus sama dengan jadwal rilis seluruh BRS.")
    assigned = [item.nama_brs for item in records if item.release_link is not None]
    if assigned:
        raise HTTPException(status_code=409, detail="Salah satu BRS sudah terdaftar pada kegiatan rilis lain.")
    return records


def ensure_draft(release: Release) -> None:
    if release.status != "draft":
        raise HTTPException(status_code=409, detail="Kegiatan yang sudah dimulai tidak dapat diubah.")


def ensure_guest_editable(release: Release) -> None:
    if release.status == "completed":
        raise HTTPException(status_code=409, detail="Daftar tamu kegiatan yang telah selesai tidak dapat diubah.")


@router.get("/eligible-brs", response_model=list[ReleaseBRSSummary])
def eligible_brs(tanggal_rilis: date, current_user: CurrentUser, db: DbSession) -> list[BRS]:
    return list(db.scalars(
        select(BRS)
        .outerjoin(ReleaseBRS, ReleaseBRS.brs_id == BRS.id)
        .where(
            BRS.status == "release_ready",
            BRS.waktu_rilis == tanggal_rilis,
            ReleaseBRS.id.is_(None),
        )
        .order_by(BRS.nama_brs)
    ))


@router.get("", response_model=list[ReleaseListResponse])
def list_releases(current_user: CurrentUser, db: DbSession) -> list[dict]:
    releases = db.scalars(release_query().order_by(Release.tanggal_rilis.desc(), Release.created_at.desc())).unique()
    return [release_payload(item) for item in releases]


@router.post("", response_model=ReleaseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_release(payload: ReleaseCreate, current_user: CurrentUser, db: DbSession) -> dict:
    require_release_manager(current_user)
    records = validate_brs(db, payload.brs_ids, payload.tanggal_rilis)
    release_id = uuid.uuid4()
    release = Release(
        id=release_id, kode_rilis=f"RLS-{payload.tanggal_rilis.year}-{release_id.hex[:6].upper()}",
        tanggal_rilis=payload.tanggal_rilis, waktu_rilis=payload.waktu_rilis,
        tempat=payload.tempat.strip(), judul_rilis=payload.judul_rilis.strip(),
        status="draft", created_by=current_user.id,
    )
    release.brs_links = [ReleaseBRS(brs_id=item.id) for item in records]
    db.add(release)
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.get("/{release_id}", response_model=ReleaseDetailResponse)
def read_release(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    return release_payload(get_release_or_404(db, release_id), detail=True)


@router.put("/{release_id}", response_model=ReleaseDetailResponse)
def update_release(
    release_id: uuid.UUID, payload: ReleaseUpdate,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_draft(release)
    if any(link.brs.waktu_rilis != payload.tanggal_rilis for link in release.brs_links):
        raise HTTPException(status_code=409, detail="Tanggal baru tidak sesuai dengan jadwal BRS yang telah dipilih.")
    release.tanggal_rilis = payload.tanggal_rilis
    release.waktu_rilis = payload.waktu_rilis
    release.tempat = payload.tempat.strip()
    release.judul_rilis = payload.judul_rilis.strip()
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_release(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_draft(release)
    db.delete(release)
    db.commit()


@router.post("/{release_id}/brs", response_model=ReleaseDetailResponse)
def add_brs(
    release_id: uuid.UUID, payload: ReleaseBRSAdd,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_draft(release)
    record = validate_brs(db, [payload.brs_id], release.tanggal_rilis)[0]
    release.brs_links.append(ReleaseBRS(brs_id=record.id))
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.delete("/{release_id}/brs/{brs_id}", response_model=ReleaseDetailResponse)
def remove_brs(
    release_id: uuid.UUID, brs_id: uuid.UUID,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_draft(release)
    link = next((item for item in release.brs_links if item.brs_id == brs_id), None)
    if link is None:
        raise HTTPException(status_code=404, detail="BRS tidak terdaftar pada kegiatan rilis ini.")
    db.delete(link)
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.post("/{release_id}/start", response_model=ReleaseDetailResponse)
def start_release(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_draft(release)
    if not release.brs_links:
        raise HTTPException(status_code=409, detail="Tambahkan minimal satu BRS sebelum memulai kegiatan.")
    release.status = "ongoing"
    release.started_at = utc_now()
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.post("/{release_id}/complete", response_model=ReleaseDetailResponse)
def complete_release(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    if release.status != "ongoing":
        raise HTTPException(status_code=409, detail="Hanya kegiatan yang sedang berlangsung dapat diselesaikan.")
    if any(link.brs.status != "release_ready" for link in release.brs_links):
        raise HTTPException(status_code=409, detail="Seluruh BRS harus tetap berstatus Siap Rilis.")
    release.status = "completed"
    release.completed_at = utc_now()
    for link in release.brs_links:
        link.brs.status = "released"
    db.commit()
    return release_payload(get_release_or_404(db, release.id), detail=True)


@router.get("/{release_id}/guests", response_model=list[GuestResponse])
def list_guests(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> list[Guest]:
    release = get_release_or_404(db, release_id)
    return sorted(release.guests, key=lambda item: item.nama)


@router.post("/{release_id}/guests", response_model=GuestResponse, status_code=status.HTTP_201_CREATED)
def create_guest(
    release_id: uuid.UUID, payload: GuestCreate,
    current_user: CurrentUser, db: DbSession,
) -> Guest:
    require_release_manager(current_user)
    release = get_release_or_404(db, release_id)
    ensure_guest_editable(release)
    guest = Guest(release_id=release.id, **{
        key: value.strip() if isinstance(value, str) else value
        for key, value in payload.model_dump().items()
    })
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


def get_guest_or_404(db: DbSession, guest_id: uuid.UUID) -> Guest:
    guest = db.scalar(select(Guest).options(selectinload(Guest.release)).where(Guest.id == guest_id))
    if guest is None:
        raise HTTPException(status_code=404, detail="Tamu tidak ditemukan.")
    return guest


@router.put("/guests/{guest_id}", response_model=GuestResponse)
def update_guest(
    guest_id: uuid.UUID, payload: GuestCreate,
    current_user: CurrentUser, db: DbSession,
) -> Guest:
    require_release_manager(current_user)
    guest = get_guest_or_404(db, guest_id)
    ensure_guest_editable(guest.release)
    for key, value in payload.model_dump().items():
        setattr(guest, key, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(guest)
    return guest


@router.delete("/guests/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(guest_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    require_release_manager(current_user)
    guest = get_guest_or_404(db, guest_id)
    ensure_guest_editable(guest.release)
    db.delete(guest)
    db.commit()

