from pathlib import Path

from app.core.exceptions import DocumentValidationError

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}


def validate_upload_metadata(filename: str | None, content_type: str | None) -> str:
    if not filename or not filename.strip():
        raise DocumentValidationError("The uploaded file must have a filename.")

    safe_display_name = Path(filename).name.strip()
    if Path(safe_display_name).suffix.lower() != ".pdf":
        raise DocumentValidationError("Only PDF files are supported in version 1.")

    if content_type and content_type.lower() not in PDF_CONTENT_TYPES:
        raise DocumentValidationError("The uploaded file does not have a PDF content type.")

    return safe_display_name


def validate_pdf_signature(header: bytes) -> None:
    if not header.startswith(b"%PDF-"):
        raise DocumentValidationError("The uploaded file is not a valid PDF.")

