import re

from app.extraction.schemas import ExtractedField, ParsedDocument
from app.models.enums import ConfidenceStatus

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip().lower()


def passage_exists(passage: str, document: ParsedDocument, page_number: int | None) -> bool:
    needle = normalize_text(passage)
    if not needle:
        return False
    if page_number is not None:
        page = next((item for item in document.pages if item.page_number == page_number), None)
        if page and needle in normalize_text(page.text):
            return True
    return needle in normalize_text(document.full_text)


def verify_field(field: ExtractedField, document: ParsedDocument) -> ExtractedField:
    if field.confidence_status == "missing" or field.value in {None, ""}:
        return ExtractedField(
            value=None,
            page_number=field.page_number,
            source_text=field.source_text,
            confidence_status="missing",
        )

    if not field.source_text or not passage_exists(field.source_text, document, field.page_number):
        return ExtractedField(
            value=field.value,
            page_number=field.page_number,
            source_text=field.source_text,
            confidence_status=ConfidenceStatus.UNSUPPORTED_EVIDENCE.value,
        )
    return ExtractedField(
        value=field.value,
        page_number=field.page_number,
        source_text=field.source_text,
        confidence_status="evidence_found",
    )
