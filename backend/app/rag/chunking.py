from __future__ import annotations

import hashlib
import re

from app.extraction.schemas import ParsedDocument
from app.rag.schemas import PreparedChunk

_HEADING = re.compile(r"^(article|section|exhibit|[A-Z][A-Z0-9 /-]{8,})$")


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def _heading_for(line: str, current: str) -> str:
    stripped = line.strip()
    if _HEADING.match(stripped):
        return stripped.title() if stripped.isupper() else stripped
    return current


def chunk_document(
    document: ParsedDocument,
    *,
    target_tokens: int = 800,
    overlap_tokens: int = 120,
) -> list[PreparedChunk]:
    lines: list[tuple[int, str]] = []
    heading = "Preamble"
    for page in document.pages:
        for raw in page.text.splitlines():
            line = raw.strip()
            if not line:
                continue
            heading = _heading_for(line, heading)
            lines.append((page.page_number, line))

    chunks: list[PreparedChunk] = []
    start = 0
    index = 0
    while start < len(lines):
        token_count = 0
        end = start
        while end < len(lines) and token_count < target_tokens:
            token_count += estimate_tokens(lines[end][1])
            end += 1
        window = lines[start:end]
        if not window:
            break
        text = "\n".join(item[1] for item in window)
        pages = [item[0] for item in window]
        section = "Preamble"
        for line in window:
            section = _heading_for(line[1], section)
        chunk_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        chunks.append(
            PreparedChunk(
                ordinal=index,
                section_heading=section,
                start_page=pages[0],
                end_page=pages[-1],
                source_text=text,
                content_hash=chunk_hash,
                token_count=estimate_tokens(text),
            )
        )
        index += 1
        if end >= len(lines):
            break
        overlap = 0
        cursor = end
        while cursor > start + 1 and overlap < overlap_tokens:
            cursor -= 1
            overlap += estimate_tokens(lines[cursor][1])
        start = max(cursor, start + 1)
    return chunks
