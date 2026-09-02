from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.brs import UserSummary

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/options", response_model=list[UserSummary])
def user_options(_current_user: CurrentUser, db: DbSession) -> list[User]:
    return list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.nama)))
