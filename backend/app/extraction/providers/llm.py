import json
import logging

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import AppError
from app.extraction.providers.base import ExtractionProvider
from app.extraction.schemas import FIELD_NAMES, LeaseExtractionResult, ParsedDocument

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You extract commercial lease fields from provided page text.
Return JSON only. Do not invent values. If a field is not explicitly present, use null
and confidence_status=missing. For found fields, copy an exact supporting passage from
the page text. Never provide legal advice or hidden reasoning."""


def _page_payload(document: ParsedDocument) -> list[dict[str, str | int]]:
    return [{"page_number": page.page_number, "text": page.text[:8000]} for page in document.pages]


class OpenAICompatibleProvider(ExtractionProvider):
    name = "openai"
    is_fixture = False

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.model_name = settings.llm_model

    def extract(
        self,
        document: ParsedDocument,
        content_hash: str,
        original_filename: str,
        sample_key: str | None = None,
    ) -> LeaseExtractionResult:
        del original_filename, sample_key
        if not self.settings.llm_api_key:
            raise AppError(
                "LLM_NOT_CONFIGURED",
                "OpenAI-compatible extraction is selected but LLM_API_KEY is not configured.",
                status_code=503,
            )

        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "fields": list(FIELD_NAMES),
                            "pages": _page_payload(document),
                            "instructions": (
                                "Extract only values supported by the page text. "
                                "Use ISO dates (YYYY-MM-DD). Use a decimal string for rent."
                            ),
                        }
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "lease_extraction",
                    "strict": True,
                    "schema": LeaseExtractionResult.model_json_schema(),
                },
            },
        }

        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                return self._complete(payload)
            except AppError:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                logger.warning(
                    "Transient LLM transport error",
                    extra={"attempt": attempt, "error_type": type(exc).__name__},
                )
        raise AppError(
            "LLM_UNAVAILABLE",
            "The extraction provider did not respond in time.",
            status_code=502,
        ) from last_error

    def _complete(self, payload: dict) -> LeaseExtractionResult:
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self.settings.llm_timeout_seconds)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            logger.warning(
                "LLM provider returned an error status",
                extra={"status_code": response.status_code},
            )
            raise AppError(
                "LLM_PROVIDER_ERROR",
                "The extraction provider rejected the request.",
                status_code=502,
            )
        if len(response.content) > self.settings.llm_max_response_bytes:
            raise AppError(
                "LLM_RESPONSE_TOO_LARGE",
                "The extraction provider response exceeded the configured size limit.",
                status_code=502,
            )
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return LeaseExtractionResult.model_validate(parsed)
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise AppError(
                "LLM_MALFORMED_RESPONSE",
                "The extraction provider returned a response that did not match the schema.",
                status_code=502,
            ) from exc
