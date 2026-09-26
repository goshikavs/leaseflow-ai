from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.core.errors import ValidationAppError


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(samples_dir: Path) -> dict:
    manifest_path = samples_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValidationAppError(
            "Sample manifest is missing. Run samples/generate_samples.py.",
            code="FIXTURE_MANIFEST_MISSING",
        )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def match_sample(
    samples_dir: Path,
    content_hash: str,
    sample_key: str | None = None,
) -> dict | None:
    samples = load_manifest(samples_dir).get("samples", [])
    by_hash = next((sample for sample in samples if sample.get("content_hash") == content_hash), None)
    if by_hash is None:
        by_hash = _match_live_file(samples_dir, samples, content_hash)
    by_key = next((sample for sample in samples if sample_key and sample.get("key") == sample_key), None)
    if by_hash and by_key and by_hash.get("key") != by_key.get("key"):
        raise ValidationAppError(
            "Fixture sample key does not match the verified content hash.",
            code="FIXTURE_ID_MISMATCH",
        )
    return by_hash or by_key


def match_sample_key(samples_dir: Path, content_hash: str) -> str | None:
    sample = match_sample(samples_dir, content_hash)
    key = sample.get("key") if sample else None
    return key if isinstance(key, str) else None


def _match_live_file(samples_dir: Path, samples: list[dict], content_hash: str) -> dict | None:
    for sample in samples:
        filename = sample.get("filename")
        if not isinstance(filename, str):
            continue
        path = samples_dir / filename
        if path.is_file() and file_sha256(path) == content_hash:
            return sample
    return None
