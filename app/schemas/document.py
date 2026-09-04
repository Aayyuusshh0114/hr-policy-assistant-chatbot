from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    content_hash: str
    mime_type: str
    size_bytes: int
    page_count: int | None
    chunk_count: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    message: str = "Document accepted for processing."
    document: DocumentResponse


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int

