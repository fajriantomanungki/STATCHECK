import uuid
from collections import Counter

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.access import require_brs_manage, require_brs_view
from app.api.deps import CurrentUser, DbSession
from app.models.brs import BRS, BRSTeam
from app.models.check import CheckResult, CheckReview, CheckRun
from app.models.document import Document
from app.models.user import utc_now
from app.schemas.check import (
    CheckResultResponse,
    CheckReviewCreate,
    CheckRunDetailResponse,
    CheckRunResponse,
)
from app.services.statcheck_engine import DOCUMENT_LABELS, run_statcheck

router = APIRouter(tags=["Checks"])
REQUIRED_DOCUMENT_TYPES = set(DOCUMENT_LABELS)
ACTION_STATUS = {"fixed": "resolved", "confirmed_correct": "confirmed", "ignored": "ignored"}


def brs_check_query():
    return select(BRS).options(
        selectinload(BRS.pjk),
        selectinload(BRS.supervisor),
        selectinload(BRS.team).selectinload(BRSTeam.user),
        selectinload(BRS.documents).selectinload(Document.contents),
    )


def run_query():
    return select(CheckRun).options(
        selectinload(CheckRun.initiator),
        selectinload(CheckRun.brs).selectinload(BRS.team),
        selectinload(CheckRun.results).selectinload(CheckResult.document),
        selectinload(CheckRun.results).selectinload(CheckResult.reviews).selectinload(CheckReview.reviewer),
    )


def get_brs_for_check(db: DbSession, brs_id: uuid.UUID) -> BRS:
    brs = db.scalar(brs_check_query().where(BRS.id == brs_id))
    if brs is None:
        raise HTTPException(status_code=404, detail="BRS tidak ditemukan.")
    return brs


def get_run_or_404(db: DbSession, run_id: uuid.UUID) -> CheckRun:
    run = db.scalar(run_query().where(CheckRun.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Hasil pemeriksaan tidak ditemukan.")
    return run


def review_payload(review: CheckReview) -> dict:
    return {
        "id": review.id, "action": review.action, "note": review.note,
        "reviewer": review.reviewer, "created_at": review.created_at,
    }


def result_payload(result: CheckResult) -> dict:
    return {
        "id": result.id, "run_id": result.run_id, "document_id": result.document_id,
        "document_type": result.document.document_type if result.document else None,
        "document_name": result.document.file_name if result.document else None,
        "brs_data_id": result.brs_data_id, "check_type": result.check_type,
        "severity": result.severity, "field_name": result.field_name,
        "expected_value": result.expected_value, "actual_value": result.actual_value,
        "message": result.message, "suggestion": result.suggestion, "status": result.status,
        "page_number": result.page_number, "context_text": result.context_text,
        "comparison_values": result.comparison_values,
        "reviews": [review_payload(review) for review in result.reviews],
        "created_at": result.created_at, "updated_at": result.updated_at,
    }


def run_payload(run: CheckRun, include_results: bool = False) -> dict:
    payload = {
        "id": run.id, "brs_id": run.brs_id, "status": run.status,
        "engine_version": run.engine_version, "total_checks": run.total_checks,
        "passed_checks": run.passed_checks, "error_count": run.error_count,
        "warning_count": run.warning_count, "suggestion_count": run.suggestion_count,
        "data_consistency_score": run.data_consistency_score,
        "cross_document_score": run.cross_document_score, "language_score": run.language_score,
        "overall_score": run.overall_score, "initiator": run.initiator,
        "started_at": run.started_at, "completed_at": run.completed_at,
    }
    if include_results:
        payload["results"] = [result_payload(result) for result in run.results]
    return payload


@router.post(
    "/brs/{brs_id}/check",
    response_model=CheckRunDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_check(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_for_check(db, brs_id)
    require_brs_manage(current_user, brs)
    active_documents = [
        document for document in brs.documents
        if document.status == "active" and document.extraction_status == "completed"
    ]
    completed_types = {document.document_type for document in active_documents}
    missing = REQUIRED_DOCUMENT_TYPES - completed_types
    if missing:
        labels = ", ".join(DOCUMENT_LABELS[item] for item in sorted(missing))
        raise HTTPException(status_code=409, detail=f"Lengkapi dan ekstrak dokumen berikut: {labels}.")

    engine = run_statcheck(active_documents)
    severity_counts = Counter(item.severity for item in engine.findings)
    check_run = CheckRun(
        brs_id=brs.id, status="completed", engine_version="rules-v2.2-indicator-periods",
        total_checks=engine.total_checks, passed_checks=engine.passed_checks,
        error_count=severity_counts["error"], warning_count=severity_counts["warning"],
        suggestion_count=severity_counts["suggestion"],
        data_consistency_score=engine.data_consistency_score,
        cross_document_score=engine.cross_document_score,
        language_score=engine.language_score, overall_score=engine.overall_score,
        initiated_by=current_user.id, completed_at=utc_now(),
    )
    check_run.results = [
        CheckResult(
            brs_id=brs.id, document_id=item.document_id, brs_data_id=item.brs_data_id,
            check_type=item.check_type, severity=item.severity, field_name=item.field_name,
            expected_value=item.expected_value, actual_value=item.actual_value,
            message=item.message, suggestion=item.suggestion, status="open",
            page_number=item.page_number, context_text=item.context_text,
            comparison_values=item.comparison_values,
        )
        for item in engine.findings
    ]
    brs.status = "pjk_review"
    db.add(check_run)
    db.commit()
    return run_payload(get_run_or_404(db, check_run.id), include_results=True)


@router.get("/brs/{brs_id}/checks", response_model=list[CheckRunResponse])
def list_check_runs(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> list[dict]:
    brs = get_brs_for_check(db, brs_id)
    require_brs_view(current_user, brs)
    query = run_query().where(CheckRun.brs_id == brs_id).order_by(CheckRun.started_at.desc())
    return [run_payload(run) for run in db.scalars(query).unique()]


@router.get("/brs/{brs_id}/checks/latest", response_model=CheckRunDetailResponse)
def latest_check_run(brs_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    brs = get_brs_for_check(db, brs_id)
    require_brs_view(current_user, brs)
    run = db.scalar(
        run_query().where(CheckRun.brs_id == brs_id).order_by(CheckRun.started_at.desc()).limit(1)
    )
    if run is None:
        raise HTTPException(status_code=404, detail="BRS ini belum pernah diperiksa.")
    return run_payload(run, include_results=True)


@router.get("/check-runs/{run_id}", response_model=CheckRunDetailResponse)
def read_check_run(run_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    run = get_run_or_404(db, run_id)
    require_brs_view(current_user, run.brs)
    return run_payload(run, include_results=True)


@router.get("/checks/{result_id}", response_model=CheckResultResponse)
def read_check_result(result_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    result = db.scalar(
        select(CheckResult).options(
            selectinload(CheckResult.document),
            selectinload(CheckResult.run).selectinload(CheckRun.brs).selectinload(BRS.team),
            selectinload(CheckResult.reviews).selectinload(CheckReview.reviewer),
        ).where(CheckResult.id == result_id)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Temuan tidak ditemukan.")
    require_brs_view(current_user, result.run.brs)
    return result_payload(result)


@router.post("/checks/{result_id}/review", response_model=CheckResultResponse)
def review_check_result(
    result_id: uuid.UUID,
    payload: CheckReviewCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = db.scalar(
        select(CheckResult).options(
            selectinload(CheckResult.document),
            selectinload(CheckResult.run).selectinload(CheckRun.brs).selectinload(BRS.team),
            selectinload(CheckResult.reviews).selectinload(CheckReview.reviewer),
        ).where(CheckResult.id == result_id)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Temuan tidak ditemukan.")
    require_brs_manage(current_user, result.run.brs)
    result.status = ACTION_STATUS[payload.action]
    result.reviews.append(CheckReview(
        reviewed_by=current_user.id, action=payload.action,
        note=payload.note.strip() if payload.note else None,
    ))
    db.commit()
    refreshed = db.scalar(
        select(CheckResult).options(
            selectinload(CheckResult.document),
            selectinload(CheckResult.reviews).selectinload(CheckReview.reviewer),
        ).where(CheckResult.id == result.id)
    )
    return result_payload(refreshed)
