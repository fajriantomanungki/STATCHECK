import uuid

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.release import QnA, Release, ReleaseBRS, ReleaseMinutes
from app.schemas.qna import MinutesResponse, MinutesUpdate
from app.services.file_storage import resolve_stored_path
from app.services.minutes_generator import generate_minutes_files

router = APIRouter(tags=["Minutes"])


def require_minutes_manager(user: object) -> None:
    if getattr(user, "user_level", None) not in {"admin", "humas"}:
        raise HTTPException(status_code=403, detail="Hanya Humas atau administrator yang dapat mengelola notulen.")


def release_minutes_query():
    return select(Release).options(
        selectinload(Release.brs_links).selectinload(ReleaseBRS.brs),
        selectinload(Release.guests),
        selectinload(Release.qna_items).selectinload(QnA.guest),
        selectinload(Release.minutes),
    )


def get_release_or_404(db: DbSession, release_id: uuid.UUID) -> Release:
    release = db.scalar(release_minutes_query().where(Release.id == release_id))
    if release is None:
        raise HTTPException(status_code=404, detail="Kegiatan rilis tidak ditemukan.")
    return release


def minutes_payload(item: ReleaseMinutes) -> dict:
    return {
        "id": item.id, "release_id": item.release_id,
        "opening": item.opening, "discussion": item.discussion,
        "notes": item.notes, "conclusion": item.conclusion,
        "content": item.content, "docx_ready": bool(item.docx_file_path),
        "pdf_ready": bool(item.pdf_file_path), "created_by": item.created_by,
        "created_at": item.created_at, "updated_at": item.updated_at,
    }


def apply_content(item: ReleaseMinutes, payload: MinutesUpdate) -> None:
    for key, value in payload.model_dump().items():
        setattr(item, key, value.strip() if value and value.strip() else None)


@router.get("/releases/{release_id}/minutes", response_model=MinutesResponse | None)
def read_minutes(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict | None:
    release = get_release_or_404(db, release_id)
    return minutes_payload(release.minutes) if release.minutes else None


@router.put("/releases/{release_id}/minutes", response_model=MinutesResponse)
def update_minutes(
    release_id: uuid.UUID, payload: MinutesUpdate,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    require_minutes_manager(current_user)
    release = get_release_or_404(db, release_id)
    if release.status == "draft":
        raise HTTPException(status_code=409, detail="Mulai kegiatan sebelum mengisi notulen.")
    item = release.minutes or ReleaseMinutes(release_id=release.id, created_by=current_user.id)
    apply_content(item, payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return minutes_payload(item)


@router.post("/releases/{release_id}/minutes/generate", response_model=MinutesResponse)
def generate_minutes(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    require_minutes_manager(current_user)
    release = get_release_or_404(db, release_id)
    if release.status == "draft":
        raise HTTPException(status_code=409, detail="Mulai kegiatan sebelum menghasilkan notulen.")
    item = release.minutes or ReleaseMinutes(release_id=release.id, created_by=current_user.id)
    db.add(item)
    db.flush()
    text, docx_path, pdf_path = generate_minutes_files(release, item)
    item.content = text
    item.docx_file_path = docx_path
    item.pdf_file_path = pdf_path
    db.commit()
    db.refresh(item)
    return minutes_payload(item)


@router.get("/releases/{release_id}/minutes/download")
def download_minutes(
    release_id: uuid.UUID, current_user: CurrentUser, db: DbSession,
    file_format: str = Query(alias="format", pattern="^(docx|pdf)$"),
) -> FileResponse:
    release = get_release_or_404(db, release_id)
    if release.minutes is None:
        raise HTTPException(status_code=404, detail="Notulen belum dibuat.")
    relative_path = release.minutes.docx_file_path if file_format == "docx" else release.minutes.pdf_file_path
    if not relative_path:
        raise HTTPException(status_code=404, detail=f"File {file_format.upper()} belum dihasilkan.")
    try:
        path = resolve_stored_path(relative_path)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Lokasi file notulen tidak valid.") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="File notulen tidak ditemukan.")
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if file_format == "docx" else "application/pdf"
    return FileResponse(path=path, media_type=media_type, filename=f"notulen_{release.kode_rilis}.{file_format}")

