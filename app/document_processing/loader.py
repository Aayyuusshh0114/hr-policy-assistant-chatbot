from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import DocumentValidationError


def extract_pdf_pages(path: Path) -> list[str]:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise DocumentValidationError("Encrypted PDFs are not supported.")
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except DocumentValidationError:
        raise
    except (PdfReadError, OSError, ValueError) as exc:
        raise DocumentValidationError("The PDF could not be read.") from exc

    if not pages:
        raise DocumentValidationError("The PDF contains no pages.")
    if not any(pages):
        raise DocumentValidationError(
            "No extractable text was found. Scanned PDFs require OCR, which is not supported yet."
        )
    return pages

