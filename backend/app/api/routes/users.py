import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.brs import UserSummary
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def require_admin(user: User) -> None:
    if user.user_level != "admin":
        raise HTTPException(status_code=403, detail="Hanya administrator yang dapat mengelola pengguna.")


@router.get("", response_model=list[UserResponse])
def list_users(current_user: CurrentUser, db: DbSession) -> list[User]:
    require_admin(current_user)
    return list(db.scalars(select(User).order_by(User.nama)))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: CurrentUser, db: DbSession) -> User:
    require_admin(current_user)
    user = User(
        nama=payload.nama.strip(),
        nik=payload.nik.strip(),
        user_level=payload.user_level,
        fungsi=payload.fungsi.strip() if payload.fungsi else None,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="NIK sudah digunakan.")
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID, payload: UserUpdate, current_user: CurrentUser, db: DbSession
) -> User:
    require_admin(current_user)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    if user.id == current_user.id and (not payload.is_active or payload.user_level != "admin"):
        raise HTTPException(status_code=409, detail="Administrator tidak dapat menonaktifkan atau menurunkan akses akunnya sendiri.")
    user.nama = payload.nama.strip()
    user.nik = payload.nik.strip()
    user.user_level = payload.user_level
    user.fungsi = payload.fungsi.strip() if payload.fungsi else None
    user.is_active = payload.is_active
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="NIK sudah digunakan.")
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    require_admin(current_user)
    if user_id == current_user.id:
        raise HTTPException(status_code=409, detail="Administrator tidak dapat menghapus akunnya sendiri.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    db.delete(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Pengguna masih terhubung dengan riwayat BRS atau rilis. Nonaktifkan pengguna melalui menu Edit.",
        )


@router.get("/options", response_model=list[UserSummary])
def user_options(_current_user: CurrentUser, db: DbSession) -> list[User]:
    return list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.nama)))
