from abc import ABC, abstractmethod

from app.extraction.schemas import LeaseExtractionResult, ParsedDocument


class ExtractionProvider(ABC):
    name: str
    model_name: str
    is_fixture: bool

    @abstractmethod
    def extract(
        self,
        document: ParsedDocument,
        content_hash: str,
        original_filename: str,
        sample_key: str | None = None,
    ) -> LeaseExtractionResult:
        raise NotImplementedError
