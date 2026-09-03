import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.access import require_brs_view
from app.api.deps import CurrentUser, DbSession
from app.models.approval import Approval
from app.models.brs import BRS, BRSTeam
from app.models.check import CheckRun
from app.schemas.approval import ApprovalNoteRequest, ApprovalWorkflowResponse

router = APIRouter(tags=["Approvals"])


def approval_brs_query():
    return select(BRS).options(
        selectinload(BRS.pjk),
        selectinload(BRS.supervisor),
        selectinload(BRS.team).selectinload(BRSTeam.user),
        selectinload(BRS.approvals).selectinload(Approval.user),
    )


def get_brs_or_404(db: DbSession, brs_id: uuid.UUID) -> BRS:
    brs = db.scalar(approval_brs_query().where(BRS.id == brs_id))
    if brs is None:
        raise HTTPException(status_code=404, detail="BRS tidak ditemukan.")
    return brs


def latest_run(db: DbSession, brs_id: uuid.UUID) -> CheckRun | None:
    return db.scalar(
        select(CheckRun)
        .options(selectinload(CheckRun.results))
        .where(CheckRun.brs_id == brs_id)
        .order_by(CheckRun.started_at.desc())
        .limit(1)
    )


def workflow_payload(db: DbSession, brs: BRS) -> dict:
    run = latest_run(db, brs.id)
    return {
        "brs_id": brs.id,
        "current_status": brs.status,
        "latest_check_id": run.id if run else None,
        "latest_score": run.overall_score if run else None,
        "open_findings": sum(result.status == "open" for result in run.results) if run else 0,
        "error_count": run.error_count if run else 0,
        "warning_count": run.warning_count if run else 0,
        "suggestion_count": run.suggestion_count if run else 0,
        "events": [
            {
                "id": event.id, "approval_level": event.approval_level,
                "action": event.action, "from_status": event.from_status,
                "to_status": event.to_status, "note": event.note,
                "user": event.user, "created_at": event.created_at,
            }
            for event in brs.approvals
        ],
    }


def clean_note(payload: ApprovalNoteRequest) -> str | None:
    return payload.note.strip() if payload.note and payload.note.strip() else None


def require_status(brs: BRS, expected: str) -> None:
    if brs.status != expected:
        raise HTTPException(
            status_code=409,
            detail=f"Aksi ini memerlukan status {expected}, sedangkan status BRS saat ini {brs.status}.",
        )


def require_pjk(user: object, brs: BRS) -> None:
    if getattr(user, "user_level", None) != "admin" and getattr(user, "id", None) != brs.pjk_id:
        raise HTTPException(status_code=403, detail="Hanya PJK BRS yang dapat melakukan aksi ini.")


def require_supervisor(user: object, brs: BRS) -> None:
    if getattr(user, "user_level", None) == "admin":
        return
    if getattr(user, "user_level", None) != "supervisor" or getattr(user, "id", None) != brs.supervisor_id:
        raise HTTPException(status_code=403, detail="Hanya Supervisor yang ditetapkan pada BRS ini yang dapat melakukan aksi ini.")


def require_ka_bps(user: object) -> None:
    if getattr(user, "user_level", None) not in {"admin", "ka_bps"}:
        raise HTTPException(status_code=403, detail="Hanya Kepala BPS yang dapat melakukan aksi ini.")


def require_submit_ka_bps(user: object, brs: BRS) -> None:
    if getattr(user, "user_level", None) == "admin":
        return
    if getattr(user, "id", None) not in {brs.pjk_id, brs.supervisor_id}:
        raise HTTPException(status_code=403, detail="Hanya PJK atau Supervisor BRS yang dapat mengirim ke Kepala BPS.")


def transition(
    db: DbSession,
    brs: BRS,
    user: object,
    level: str,
    action: str,
    to_status: str,
    note: str | None,
) -> dict:
    from_status = brs.status
    brs.status = to_status
    db.add(Approval(
        brs_id=brs.id, user_id=getattr(user, "id"), approval_level=level,
        action=action, from_status=from_status, to_status=to_status, note=note,
    ))
    db.commit()
    return workflow_payload(db, get_brs_or_404(db, brs.id))


@router.get("/brs/{brs_id}/approval", response_model=ApprovalWorkflowResponse)
def read_workflow(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_brs_view(current_user, brs)
    return workflow_payload(db, brs)


@router.post("/brs/{brs_id}/submit-supervisor", response_model=ApprovalWorkflowResponse)
def submit_supervisor(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_pjk(current_user, brs)
    require_status(brs, "pjk_review")
    if brs.supervisor_id is None:
        raise HTTPException(status_code=409, detail="Tetapkan Supervisor sebelum mengirim BRS.")
    run = latest_run(db, brs.id)
    if run is None:
        raise HTTPException(status_code=409, detail="Jalankan STATCHECK sebelum mengirim ke Supervisor.")
    open_findings = sum(result.status == "open" for result in run.results)
    if open_findings:
        raise HTTPException(
            status_code=409,
            detail=f"Tindak lanjuti {open_findings} temuan yang masih terbuka sebelum mengirim BRS.",
        )
    return transition(db, brs, current_user, "pjk", "submitted", "pjk_submitted", clean_note(payload))


@router.post("/brs/{brs_id}/supervisor/start-review", response_model=ApprovalWorkflowResponse)
def start_supervisor_review(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_supervisor(current_user, brs)
    require_status(brs, "pjk_submitted")
    return transition(db, brs, current_user, "supervisor", "review_started", "supervisor_review", None)


@router.post("/brs/{brs_id}/supervisor/approve", response_model=ApprovalWorkflowResponse)
def supervisor_approve(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_supervisor(current_user, brs)
    require_status(brs, "supervisor_review")
    return transition(db, brs, current_user, "supervisor", "approved", "supervisor_approved", clean_note(payload))


@router.post("/brs/{brs_id}/supervisor/revision", response_model=ApprovalWorkflowResponse)
def supervisor_revision(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_supervisor(current_user, brs)
    require_status(brs, "supervisor_review")
    note = clean_note(payload)
    if not note:
        raise HTTPException(status_code=422, detail="Catatan wajib diisi ketika mengembalikan BRS.")
    return transition(db, brs, current_user, "supervisor", "revision", "supervisor_revision", note)


@router.post("/brs/{brs_id}/submit-ka-bps", response_model=ApprovalWorkflowResponse)
def submit_ka_bps(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_submit_ka_bps(current_user, brs)
    require_status(brs, "supervisor_approved")
    return transition(db, brs, current_user, "supervisor", "submitted_to_ka_bps", "ka_bps_review", clean_note(payload))


@router.post("/brs/{brs_id}/ka-bps/approve", response_model=ApprovalWorkflowResponse)
def ka_bps_approve(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_ka_bps(current_user)
    require_status(brs, "ka_bps_review")
    return transition(db, brs, current_user, "ka_bps", "approved", "release_ready", clean_note(payload))


@router.post("/brs/{brs_id}/ka-bps/revision", response_model=ApprovalWorkflowResponse)
def ka_bps_revision(
    brs_id: uuid.UUID, payload: ApprovalNoteRequest,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_ka_bps(current_user)
    require_status(brs, "ka_bps_review")
    note = clean_note(payload)
    if not note:
        raise HTTPException(status_code=422, detail="Catatan wajib diisi ketika mengembalikan BRS.")
    return transition(db, brs, current_user, "ka_bps", "revision", "ka_bps_revision", note)
