from pathlib import Path

from app.core.errors import ValidationAppError
from app.extraction.providers.base import ExtractionProvider
from app.extraction.sample_catalog import match_sample
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

    def extract(
        self,
        document: ParsedDocument,
        content_hash: str,
        original_filename: str,
        sample_key: str | None = None,
    ) -> LeaseExtractionResult:
        del original_filename  # Filename is never a fixture selector.
        sample = match_sample(self.samples_dir, content_hash, sample_key)
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
