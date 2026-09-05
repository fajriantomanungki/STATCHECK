import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.api.access import require_brs_manage, require_brs_view
from app.api.deps import CurrentUser, DbSession
from app.api.routes.brs import get_brs_or_404
from app.core.config import settings
from app.models.brs import BRS
from app.models.document import Document, DocumentContent
from app.schemas.document import DocumentDetailResponse, DocumentResponse
from app.services.document_extractor import DocumentExtractionError, SUPPORTED_EXTENSIONS, extract_document
from app.services.file_storage import resolve_stored_path, store_file
from app.services.presentation_indicator_extractor import sync_presentation_indicators

router = APIRouter(tags=["Documents"])

DOCUMENT_TYPES = {"bahan_publikasi", "bahan_paparan", "narasi_pimpinan"}
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def document_query():
    return select(Document).options(
        selectinload(Document.uploader),
        selectinload(Document.contents),
        selectinload(Document.brs).selectinload(BRS.team),
    )


def get_document_or_404(db: DbSession, document_id: uuid.UUID) -> Document:
    document = db.scalar(document_query().where(Document.id == document_id))
    if document is None:
        raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan.")
    return document


def document_payload(document: Document, include_contents: bool = False) -> dict:
    payload = {
        "id": document.id,
        "brs_id": document.brs_id,
        "document_type": document.document_type,
        "file_name": document.file_name,
        "file_extension": document.file_extension,
        "mime_type": document.mime_type,
        "file_size": document.file_size,
        "checksum_sha256": document.checksum_sha256,
        "version": document.version,
        "status": document.status,
        "extraction_status": document.extraction_status,
        "extraction_error": document.extraction_error,
        "page_count": document.page_count,
        "extracted_char_count": sum(len(item.text_content) for item in document.contents),
        "uploaded_by": document.uploaded_by,
        "uploader": document.uploader,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }
    if include_contents:
        payload["contents"] = document.contents
    return payload


def refresh_brs_document_status(db: DbSession, brs: BRS) -> None:
    active_documents = list(
        db.scalars(select(Document).where(Document.brs_id == brs.id, Document.status == "active"))
    )
    completed_types = {
        document.document_type
        for document in active_documents
        if document.extraction_status == "completed"
    }
    brs.status = "documents_uploaded" if DOCUMENT_TYPES.issubset(completed_types) else "draft"


@router.get("/brs/{brs_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    brs_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    include_archived: bool = False,
) -> list[dict]:
    brs = get_brs_or_404(db, brs_id)
    require_brs_view(current_user, brs)
    query = document_query().where(Document.brs_id == brs_id)
    if not include_archived:
        query = query.where(Document.status == "active")
    query = query.order_by(Document.document_type, Document.version.desc())
    return [document_payload(item) for item in db.scalars(query).unique()]


@router.post(
    "/brs/{brs_id}/documents",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    brs_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    document_type: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    brs = get_brs_or_404(db, brs_id)
    require_brs_manage(current_user, brs)
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(status_code=422, detail="Jenis dokumen tidak valid.")
    if not file.filename:
        raise HTTPException(status_code=422, detail="Nama file tidak tersedia.")

    extension = Path(file.filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Format file harus PDF, PPTX, atau DOCX.")
    content = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if not content:
        raise HTTPException(status_code=422, detail="File yang diunggah kosong.")
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Ukuran file melebihi batas {settings.max_upload_size_mb} MB.",
        )

    latest_version = db.scalar(
        select(func.max(Document.version)).where(
            Document.brs_id == brs_id,
            Document.document_type == document_type,
        )
    ) or 0
    version = latest_version + 1

    try:
        extraction = extract_document(content, file.filename)
        extraction_status = "completed"
        extraction_error = None
    except DocumentExtractionError as exc:
        extraction = None
        extraction_status = "failed"
        extraction_error = str(exc)

    stored = store_file(content, brs.id, document_type, version, extension)
    try:
        previous = list(
            db.scalars(
                select(Document).where(
                    Document.brs_id == brs_id,
                    Document.document_type == document_type,
                    Document.status == "active",
                )
            )
        )
        for old_document in previous:
            old_document.status = "archived"

        document = Document(
            brs_id=brs.id,
            document_type=document_type,
            file_name=Path(file.filename).name,
            stored_name=stored.stored_name,
            file_path=stored.relative_path,
            file_extension=extension,
            mime_type=MIME_TYPES[extension],
            file_size=len(content),
            checksum_sha256=stored.checksum_sha256,
            version=version,
            status="active",
            extraction_status=extraction_status,
            extraction_error=extraction_error,
            page_count=extraction.page_count if extraction else 0,
            uploaded_by=current_user.id,
        )
        if extraction:
            document.contents = [
                DocumentContent(
                    page_number=section.page_number,
                    section_label=section.section_label,
                    text_content=section.text_content,
                )
                for section in extraction.sections
            ]
        db.add(document)
        db.flush()
        if document_type == "bahan_paparan":
            sync_presentation_indicators(db, document, current_user.id)
        refresh_brs_document_status(db, brs)
        db.commit()
    except Exception:
        db.rollback()
        if stored.absolute_path.exists():
            stored.absolute_path.unlink()
        raise

    saved = get_document_or_404(db, document.id)
    return document_payload(saved, include_contents=True)


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
def read_document(document_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    document = get_document_or_404(db, document_id)
    require_brs_view(current_user, document.brs)
    return document_payload(document, include_contents=True)


@router.get("/documents/{document_id}/download")
def download_document(document_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> FileResponse:
    document = get_document_or_404(db, document_id)
    require_brs_view(current_user, document.brs)
    try:
        path = resolve_stored_path(document.file_path)
    except ValueError:
        raise HTTPException(status_code=500, detail="Lokasi file tidak valid.")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File dokumen tidak ditemukan pada penyimpanan.")
    return FileResponse(path=path, filename=document.file_name, media_type=document.mime_type)


@router.post("/documents/{document_id}/reextract", response_model=DocumentDetailResponse)
def reextract_document(document_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> dict:
    document = get_document_or_404(db, document_id)
    require_brs_manage(current_user, document.brs)
    try:
        path = resolve_stored_path(document.file_path)
        extraction = extract_document(path.read_bytes(), document.file_name)
    except (ValueError, OSError, DocumentExtractionError) as exc:
        document.extraction_status = "failed"
        document.extraction_error = str(exc)
        document.page_count = 0
        db.execute(delete(DocumentContent).where(DocumentContent.document_id == document.id))
        db.expire(document, ["contents"])
        if document.document_type == "bahan_paparan" and document.status == "active":
            sync_presentation_indicators(db, document, current_user.id)
        refresh_brs_document_status(db, document.brs)
        db.commit()
        return document_payload(get_document_or_404(db, document.id), include_contents=True)

    db.execute(delete(DocumentContent).where(DocumentContent.document_id == document.id))
    document.contents = [
        DocumentContent(
            document_id=document.id,
            page_number=section.page_number,
            section_label=section.section_label,
            text_content=section.text_content,
        )
        for section in extraction.sections
    ]
    document.extraction_status = "completed"
    document.extraction_error = None
    document.page_count = extraction.page_count
    if document.document_type == "bahan_paparan" and document.status == "active":
        sync_presentation_indicators(db, document, current_user.id)
    refresh_brs_document_status(db, document.brs)
    db.commit()
    return document_payload(get_document_or_404(db, document.id), include_contents=True)
