import json
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.brs import BRS, BRSData
from app.models.document import Document
from app.models.release import Guest, QnA, Release, ReleaseBRS
from app.models.user import utc_now
from app.schemas.qna import AIStatusResponse, QnAAnswersUpdate, QnACreate, QnAFinalize, QnAResponse
from app.services.qa_grounding import (
    AIProviderError,
    AIUnavailableError,
    build_grounding_context,
    generate_grounded_answer,
)

router = APIRouter(tags=["Q&A"])


def qna_query():
    return select(QnA).options(
        selectinload(QnA.guest), selectinload(QnA.finalizer),
        selectinload(QnA.release).selectinload(Release.brs_links).selectinload(ReleaseBRS.brs),
    )


def get_qna_or_404(db: DbSession, qna_id: uuid.UUID) -> QnA:
    item = db.scalar(qna_query().where(QnA.id == qna_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Pertanyaan tidak ditemukan.")
    return item


def get_release_or_404(db: DbSession, release_id: uuid.UUID) -> Release:
    release = db.scalar(
        select(Release).options(
            selectinload(Release.brs_links).selectinload(ReleaseBRS.brs),
            selectinload(Release.qna_items).selectinload(QnA.guest),
        ).where(Release.id == release_id)
    )
    if release is None:
        raise HTTPException(status_code=404, detail="Kegiatan rilis tidak ditemukan.")
    return release


def ensure_session_active(release: Release) -> None:
    if release.status != "ongoing":
        raise HTTPException(status_code=409, detail="Q&A hanya dapat diubah saat kegiatan sedang berlangsung.")


def is_manager(user: object) -> bool:
    return getattr(user, "user_level", None) in {"admin", "humas"}


def is_assigned(user: object, release: Release, role: str | None = None) -> bool:
    user_id = getattr(user, "id", None)
    for link in release.brs_links:
        if role in {None, "pjk"} and link.brs.pjk_id == user_id:
            return True
        if role in {None, "supervisor"} and link.brs.supervisor_id == user_id:
            return True
    return False


def require_contributor(user: object, release: Release) -> None:
    if not is_manager(user) and not is_assigned(user, release):
        raise HTTPException(status_code=403, detail="Anda tidak ditetapkan sebagai pengelola, PJK, atau Supervisor kegiatan ini.")


def qna_payload(item: QnA) -> dict:
    try:
        sources = json.loads(item.ai_sources) if item.ai_sources else []
    except json.JSONDecodeError:
        sources = []
    return {
        "id": item.id, "release_id": item.release_id, "guest": item.guest,
        "question": item.question, "ai_answer": item.ai_answer,
        "supervisor_answer": item.supervisor_answer, "pjk_answer": item.pjk_answer,
        "final_answer": item.final_answer, "ai_model": item.ai_model,
        "ai_sources": sources, "generated_at": item.generated_at,
        "finalizer": item.finalizer, "finalized_at": item.finalized_at,
        "created_at": item.created_at, "updated_at": item.updated_at,
    }


@router.get("/ai/status", response_model=AIStatusResponse)
def ai_status(current_user: CurrentUser) -> AIStatusResponse:
    return AIStatusResponse(enabled=bool(settings.openai_api_key), model=settings.openai_model)


@router.get("/releases/{release_id}/qna", response_model=list[QnAResponse])
def list_qna(release_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> list[dict]:
    release = get_release_or_404(db, release_id)
    records = db.scalars(qna_query().where(QnA.release_id == release.id).order_by(QnA.created_at)).unique()
    return [qna_payload(item) for item in records]


@router.post("/releases/{release_id}/qna", response_model=QnAResponse, status_code=status.HTTP_201_CREATED)
def create_qna(
    release_id: uuid.UUID, payload: QnACreate,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    release = get_release_or_404(db, release_id)
    ensure_session_active(release)
    if not is_manager(current_user):
        raise HTTPException(status_code=403, detail="Hanya Humas atau administrator yang dapat mencatat pertanyaan.")
    if payload.guest_id:
        guest = db.scalar(select(Guest).where(Guest.id == payload.guest_id, Guest.release_id == release.id))
        if guest is None:
            raise HTTPException(status_code=422, detail="Penanya tidak terdaftar pada kegiatan ini.")
    item = QnA(
        release_id=release.id, guest_id=payload.guest_id,
        question=payload.question.strip(),
    )
    db.add(item)
    db.commit()
    return qna_payload(get_qna_or_404(db, item.id))


@router.put("/qna/{qna_id}", response_model=QnAResponse)
def update_answers(
    qna_id: uuid.UUID, payload: QnAAnswersUpdate,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    item = get_qna_or_404(db, qna_id)
    ensure_session_active(item.release)
    if not payload.model_fields_set:
        raise HTTPException(status_code=422, detail="Pilih jawaban yang akan diperbarui.")
    if "supervisor_answer" in payload.model_fields_set:
        if current_user.user_level != "admin" and not is_assigned(current_user, item.release, "supervisor"):
            raise HTTPException(status_code=403, detail="Hanya Supervisor yang ditetapkan dapat mengisi jawaban Supervisor.")
        item.supervisor_answer = payload.supervisor_answer.strip() if payload.supervisor_answer else None
    if "pjk_answer" in payload.model_fields_set:
        if current_user.user_level != "admin" and not is_assigned(current_user, item.release, "pjk"):
            raise HTTPException(status_code=403, detail="Hanya PJK yang ditetapkan dapat mengisi jawaban PJK.")
        item.pjk_answer = payload.pjk_answer.strip() if payload.pjk_answer else None
    db.commit()
    return qna_payload(get_qna_or_404(db, item.id))


@router.post("/qna/{qna_id}/generate-answer", response_model=QnAResponse)
def generate_answer(qna_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    item = get_qna_or_404(db, qna_id)
    ensure_session_active(item.release)
    require_contributor(current_user, item.release)
    release = db.scalar(
        select(Release).options(
            selectinload(Release.brs_links).selectinload(ReleaseBRS.brs).selectinload(BRS.data).selectinload(BRSData.indicator),
            selectinload(Release.brs_links).selectinload(ReleaseBRS.brs).selectinload(BRS.presentation_indicators),
            selectinload(Release.brs_links).selectinload(ReleaseBRS.brs).selectinload(BRS.documents).selectinload(Document.contents),
        ).where(Release.id == item.release_id)
    )
    context = build_grounding_context(release, item.question)
    try:
        answer, model = generate_grounded_answer(item.question, context)
    except AIUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    item.ai_answer = answer
    item.ai_model = model
    item.ai_sources = json.dumps(context.sources, ensure_ascii=False)
    item.generated_at = utc_now()
    db.commit()
    return qna_payload(get_qna_or_404(db, item.id))


@router.post("/qna/{qna_id}/finalize", response_model=QnAResponse)
def finalize_answer(
    qna_id: uuid.UUID, payload: QnAFinalize,
    current_user: CurrentUser, db: DbSession,
) -> dict:
    item = get_qna_or_404(db, qna_id)
    ensure_session_active(item.release)
    require_contributor(current_user, item.release)
    item.final_answer = payload.final_answer.strip()
    item.finalized_by = current_user.id
    item.finalized_at = utc_now()
    db.commit()
    return qna_payload(get_qna_or_404(db, item.id))


@router.delete("/qna/{qna_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_qna(qna_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    item = get_qna_or_404(db, qna_id)
    ensure_session_active(item.release)
    if not is_manager(current_user):
        raise HTTPException(status_code=403, detail="Hanya Humas atau administrator yang dapat menghapus pertanyaan.")
    db.delete(item)
    db.commit()
