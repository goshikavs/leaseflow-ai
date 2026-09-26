import logging
from pathlib import Path

import fitz

from app.core.errors import ValidationAppError
from app.extraction.schemas import ParsedDocument, ParsedPage

logger = logging.getLogger(__name__)

PDF_HEADER = b"%PDF-"


def validate_pdf_bytes(data: bytes, filename: str, max_bytes: int) -> None:
    if not filename.lower().endswith(".pdf"):
        raise ValidationAppError("Only PDF files are accepted.", code="INVALID_FILE_TYPE")
    if len(data) == 0:
        raise ValidationAppError("Uploaded file is empty.", code="EMPTY_FILE")
    if len(data) > max_bytes:
        raise ValidationAppError(
            f"File exceeds the configured size limit of {max_bytes} bytes.",
            code="FILE_TOO_LARGE",
        )
    if not data.startswith(PDF_HEADER):
        raise ValidationAppError(
            "File content is not a valid PDF.",
            code="INVALID_PDF_CONTENT",
        )


def parse_pdf(path: Path) -> ParsedDocument:
    try:
        document = fitz.open(path)
    except Exception as exc:  # pragma: no cover - defensive parser boundary
        raise ValidationAppError("The PDF could not be parsed.", code="PDF_PARSE_ERROR") from exc

    try:
        pages = [
            ParsedPage(page_number=index + 1, text=page.get_text("text") or "") for index, page in enumerate(document)
        ]
    finally:
        document.close()

    if not pages:
        raise ValidationAppError("The PDF contains no readable pages.", code="PDF_EMPTY")
    return ParsedDocument(page_count=len(pages), pages=pages)
