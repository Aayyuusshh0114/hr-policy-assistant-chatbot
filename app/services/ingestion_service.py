import hashlib
import logging
import sqlite3
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentValidationError,
    DuplicateDocumentError,
)
from app.document_processing.loader import extract_pdf_pages
from app.document_processing.splitter import TextSplitter
from app.document_processing.validator import validate_pdf_signature, validate_upload_metadata
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse
from app.services.index_service import IndexService

logger = logging.getLogger(__name__)
COPY_BUFFER_SIZE = 1024 * 1024


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        repository: DocumentRepository,
        index_service: IndexService,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.index_service = index_service
        self.splitter = TextSplitter(settings.chunk_size, settings.chunk_overlap)

    async def accept_upload(self, upload: UploadFile) -> DocumentResponse:
        original_filename = validate_upload_metadata(upload.filename, upload.content_type)
        document_id = str(uuid4())
        stored_filename = f"{document_id}.pdf"
        target = self.settings.resolved_upload_directory / stored_filename
        temporary_target = target.with_suffix(".part")
        maximum_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        size_bytes = 0
        digest = hashlib.sha256()
        header = b""

        try:
            with temporary_target.open("xb") as destination:
                while data := await upload.read(COPY_BUFFER_SIZE):
                    if not header:
                        header = data[:8]
                        validate_pdf_signature(header)
                    size_bytes += len(data)
                    if size_bytes > maximum_bytes:
                        raise DocumentValidationError(
                            "The PDF exceeds the "
                            f"{self.settings.max_upload_size_mb} MB upload limit."
                        )
                    digest.update(data)
                    destination.write(data)

            if size_bytes == 0:
                raise DocumentValidationError("The uploaded PDF is empty.")

            content_hash = digest.hexdigest()
            duplicate = self.repository.find_by_hash(content_hash)
            if duplicate:
                raise DuplicateDocumentError(duplicate.id)

            temporary_target.replace(target)
            try:
                return self.repository.create_document(
                    document_id=document_id,
                    original_filename=original_filename,
                    stored_filename=stored_filename,
                    content_hash=content_hash,
                    mime_type="application/pdf",
                    size_bytes=size_bytes,
                )
            except sqlite3.IntegrityError as exc:
                duplicate = self.repository.find_by_hash(content_hash)
                if duplicate:
                    raise DuplicateDocumentError(duplicate.id) from exc
                raise
        except Exception:
            temporary_target.unlink(missing_ok=True)
            if target.exists() and self.repository.get_document(document_id) is None:
                target.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def process_document(self, document_id: str) -> None:
        stored_filename = self.repository.get_stored_filename(document_id)
        if stored_filename is None:
            logger.warning("document_processing_skipped_missing_record", extra={"id": document_id})
            return

        path = self.settings.resolved_upload_directory / stored_filename
        try:
            pages = extract_pdf_pages(path)
            page_chunks = self.splitter.split_pages(pages)
            if not any(page_chunks):
                raise DocumentValidationError("No usable text chunks were produced from the PDF.")
            self.repository.save_chunks(document_id, page_chunks)
            self.index_service.rebuild()
            self.repository.mark_ready(document_id)
            logger.info("document_processing_complete", extra={"id": document_id})
        except DocumentValidationError as exc:
            self.repository.mark_failed(document_id, str(exc))
            logger.info("document_processing_failed", extra={"id": document_id})
        except Exception:
            self.repository.mark_failed(document_id, "Document processing failed unexpectedly.")
            logger.exception("document_processing_failed_unexpected", extra={"id": document_id})

    def delete_document(self, document_id: str) -> None:
        stored_filename = self.repository.get_stored_filename(document_id)
        if stored_filename is None:
            raise DocumentNotFoundError("Document not found.")

        if not self.repository.delete_document(document_id):
            raise DocumentNotFoundError("Document not found.")
        (self.settings.resolved_upload_directory / stored_filename).unlink(missing_ok=True)
        self.index_service.rebuild()
