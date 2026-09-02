from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.access import can_view_brs
from app.api.deps import CurrentUser, DbSession
from app.models.brs import BRS, BRSData
from app.models.indicator import Indicator
from app.schemas.brs import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(current_user: CurrentUser, db: DbSession) -> DashboardSummary:
    brs_records = list(db.scalars(select(BRS).options(selectinload(BRS.team))))
    visible = [brs for brs in brs_records if can_view_brs(current_user, brs)]
    visible_ids = [brs.id for brs in visible]
    total_data = 0
    if visible_ids:
        total_data = db.scalar(select(func.count()).select_from(BRSData).where(BRSData.brs_id.in_(visible_ids))) or 0
    total_indicators = db.scalar(select(func.count()).select_from(Indicator).where(Indicator.is_active.is_(True))) or 0
    return DashboardSummary(
        total_brs=len(visible),
        draft_brs=sum(brs.status == "draft" for brs in visible),
        total_indicators=total_indicators,
        total_brs_data=total_data,
    )
