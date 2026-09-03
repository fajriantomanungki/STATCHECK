from fastapi import HTTPException, status

from app.models.brs import BRS
from app.models.user import User


FULL_ACCESS_ROLES = {"admin", "ka_bps", "humas"}
EDITABLE_BRS_STATUSES = {"draft", "data_completed", "documents_uploaded", "pjk_review"}


def can_view_brs(user: User, brs: BRS) -> bool:
    if user.user_level in FULL_ACCESS_ROLES:
        return True
    if brs.pjk_id == user.id or brs.supervisor_id == user.id:
        return True
    return any(member.user_id == user.id for member in brs.team)


def require_brs_view(user: User, brs: BRS) -> None:
    if not can_view_brs(user, brs):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Anda tidak memiliki akses ke BRS ini.")


def require_brs_manage(user: User, brs: BRS) -> None:
    if user.user_level != "admin" and brs.pjk_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya PJK BRS yang dapat mengubah data ini.")
    if brs.status not in EDITABLE_BRS_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="BRS sudah memasuki tahap pemeriksaan dan tidak dapat diubah.",
        )
