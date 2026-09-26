import hashlib
import re
from pathlib import Path

from app.core.ids import new_id

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_original_name(filename: str) -> str:
    name = Path(filename).name
    cleaned = _UNSAFE.sub("_", name).strip("._")
    return cleaned or "document.pdf"


def stored_filename() -> str:
    return f"{new_id()}.pdf"


def write_document(storage_dir: Path, data: bytes) -> Path:
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / stored_filename()
    path.write_bytes(data)
    return path
