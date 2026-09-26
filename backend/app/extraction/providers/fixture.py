import json
from pathlib import Path

from app.core.errors import ValidationAppError
from app.extraction.providers.base import ExtractionProvider
from app.extraction.schemas import FIELD_NAMES, ExtractedField, LeaseExtractionResult, ParsedDocument

MISSING_FIELD = ExtractedField(value=None, page_number=None, source_text=None, confidence_status="missing")


def _missing_result() -> LeaseExtractionResult:
    return LeaseExtractionResult.model_validate({name: MISSING_FIELD.model_dump() for name in FIELD_NAMES})


class FixtureExtractionProvider(ExtractionProvider):
    name = "fixture"
    model_name = "deterministic-sample-fixture"
    is_fixture = True

    def __init__(self, samples_dir: Path) -> None:
        self.samples_dir = samples_dir
        self.manifest_path = samples_dir / "manifest.json"

    def extract(
        self,
        document: ParsedDocument,
        content_hash: str,
        original_filename: str,
        sample_key: str | None = None,
    ) -> LeaseExtractionResult:
        del original_filename  # Filename is never a fixture selector.
        manifest = self._load_manifest()
        sample = self._match_sample(manifest, content_hash, sample_key)
        if sample is None:
            return _missing_result()

        result = LeaseExtractionResult.model_validate(sample["extraction"])
        for field in result.field_map().values():
            if field.source_text and field.source_text not in document.full_text:
                raise ValidationAppError(
                    "Fixture extraction does not match the parsed sample document text.",
                    code="FIXTURE_TEXT_MISMATCH",
                )
        return result

    def _load_manifest(self) -> dict:
        if not self.manifest_path.exists():
            raise ValidationAppError(
                "Sample manifest is missing. Run samples/generate_samples.py.",
                code="FIXTURE_MANIFEST_MISSING",
            )
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _match_sample(self, manifest: dict, content_hash: str, sample_key: str | None) -> dict | None:
        samples = manifest.get("samples", [])
        by_hash = next((sample for sample in samples if sample.get("content_hash") == content_hash), None)
        by_key = next((sample for sample in samples if sample_key and sample.get("key") == sample_key), None)
        if by_hash and by_key and by_hash.get("key") != by_key.get("key"):
            raise ValidationAppError(
                "Fixture sample key does not match the verified content hash.",
                code="FIXTURE_ID_MISMATCH",
            )
        return by_hash or by_key
