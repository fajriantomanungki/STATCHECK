import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.models.indicator import Indicator
from app.schemas.indicator import IndicatorCreate, IndicatorResponse, IndicatorUpdate

router = APIRouter(prefix="/indicators", tags=["Indicators"])


def require_admin(user: object) -> None:
    if getattr(user, "user_level", None) != "admin":
        raise HTTPException(status_code=403, detail="Hanya administrator yang dapat mengelola master indikator.")


@router.get("", response_model=list[IndicatorResponse])
def list_indicators(_current_user: CurrentUser, db: DbSession, active_only: bool = False) -> list[Indicator]:
    query = select(Indicator)
    if active_only:
        query = query.where(Indicator.is_active.is_(True))
    return list(db.scalars(query.order_by(Indicator.kategori, Indicator.nama_indikator)))


@router.post("", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
def create_indicator(payload: IndicatorCreate, current_user: CurrentUser, db: DbSession) -> Indicator:
    require_admin(current_user)
    indicator = Indicator(**payload.model_dump())
    db.add(indicator)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nama indikator sudah terdaftar.")
    db.refresh(indicator)
    return indicator


@router.put("/{indicator_id}", response_model=IndicatorResponse)
def update_indicator(indicator_id: uuid.UUID, payload: IndicatorUpdate, current_user: CurrentUser, db: DbSession) -> Indicator:
    require_admin(current_user)
    indicator = db.get(Indicator, indicator_id)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indikator tidak ditemukan.")
    for key, value in payload.model_dump().items():
        setattr(indicator, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nama indikator sudah digunakan.")
    db.refresh(indicator)
    return indicator


@router.delete("/{indicator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_indicator(
    indicator_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    require_admin(current_user)
    indicator = db.get(Indicator, indicator_id)
    if indicator is None:
        raise HTTPException(status_code=404, detail="Indikator tidak ditemukan.")
    db.delete(indicator)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Indikator masih digunakan pada data BRS. Nonaktifkan indikator melalui menu Edit.",
        )
