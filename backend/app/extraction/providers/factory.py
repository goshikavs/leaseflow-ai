from app.core.config import Settings
from app.extraction.providers.base import ExtractionProvider
from app.extraction.providers.fixture import FixtureExtractionProvider
from app.extraction.providers.llm import OpenAICompatibleProvider


def get_extraction_provider(settings: Settings) -> ExtractionProvider:
    if settings.extraction_provider == "openai":
        return OpenAICompatibleProvider(settings)
    return FixtureExtractionProvider(settings.resolved_samples_dir)
