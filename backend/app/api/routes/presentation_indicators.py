import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.access import require_brs_manage, require_brs_view
from app.api.deps import CurrentUser, DbSession
from app.api.routes.brs import get_brs_or_404
from app.models.document import Document
from app.models.presentation_indicator import PresentationIndicator
from app.schemas.presentation_indicator import (
    PresentationIndicatorResponse,
    PresentationIndicatorUpdate,
)
from app.services.presentation_indicator_extractor import sync_presentation_indicators

router = APIRouter(tags=["Presentation Indicators"])


def _active_sources(db: DbSession, brs_id: uuid.UUID) -> list[Document]:
    return list(db.scalars(
        select(Document)
        .options(selectinload(Document.contents))
        .where(
            Document.brs_id == brs_id,
            Document.document_type.in_({"bahan_paparan", "narasi_pimpinan"}),
            Document.status == "active",
        )
        .order_by(Document.version.desc())
    ).unique())


@router.get(
    "/brs/{brs_id}/presentation-indicators",
    response_model=list[PresentationIndicatorResponse],
)
def list_presentation_indicators(
    brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> list[PresentationIndicator]:
    brs = get_brs_or_404(db, brs_id)
    require_brs_view(current_user, brs)
    return list(db.scalars(
        select(PresentationIndicator)
        .options(selectinload(PresentationIndicator.document))
        .where(PresentationIndicator.brs_id == brs_id)
        .order_by(PresentationIndicator.created_at, PresentationIndicator.page_number)
    ))


@router.post(
    "/brs/{brs_id}/presentation-indicators/refresh",
    response_model=list[PresentationIndicatorResponse],
)
def refresh_presentation_indicators(
    brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> list[PresentationIndicator]:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    documents = _active_sources(db, brs_id)
    if not documents:
        raise HTTPException(
            status_code=409,
            detail="Unggah Bahan Paparan atau Narasi Pimpinan terlebih dahulu.",
        )
    completed = [item for item in documents if item.extraction_status == "completed"]
    if not completed:
        raise HTTPException(status_code=409, detail="Ekstraksi dokumen sumber belum berhasil.")
    sync_presentation_indicators(db, completed[0], current_user.id)
    db.commit()
    return list(db.scalars(
        select(PresentationIndicator)
        .options(selectinload(PresentationIndicator.document))
        .where(PresentationIndicator.brs_id == brs_id)
        .order_by(PresentationIndicator.created_at, PresentationIndicator.page_number)
    ))


@router.put(
    "/brs/{brs_id}/presentation-indicators/{item_id}",
    response_model=PresentationIndicatorResponse,
)
def update_presentation_indicator(
    brs_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: PresentationIndicatorUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> PresentationIndicator:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    item = db.scalar(select(PresentationIndicator).where(
        PresentationIndicator.id == item_id,
        PresentationIndicator.brs_id == brs_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Data hasil ekstraksi tidak ditemukan.")
    item.analysis = payload.analysis.strip() if payload.analysis else None
    item.phenomenon = payload.phenomenon.strip() if payload.phenomenon else None
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/brs/{brs_id}/presentation-indicators/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_presentation_indicator(
    brs_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    item = db.scalar(select(PresentationIndicator).where(
        PresentationIndicator.id == item_id,
        PresentationIndicator.brs_id == brs_id,
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Data hasil ekstraksi tidak ditemukan.")
    db.delete(item)
    db.commit()
