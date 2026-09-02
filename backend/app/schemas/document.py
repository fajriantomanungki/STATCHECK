import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.brs import UserSummary


class DocumentContentResponse(BaseModel):
    id: uuid.UUID
    page_number: int
    section_label: str
    text_content: str

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: uuid.UUID
    brs_id: uuid.UUID
    document_type: str
    file_name: str
    file_extension: str
    mime_type: str
    file_size: int
    checksum_sha256: str
    version: int
    status: str
    extraction_status: str
    extraction_error: str | None
    page_count: int
    extracted_char_count: int
    uploaded_by: uuid.UUID
    uploader: UserSummary
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    contents: list[DocumentContentResponse]
