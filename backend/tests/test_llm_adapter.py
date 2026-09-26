import json

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.extraction.providers.llm import OpenAICompatibleProvider
from app.extraction.schemas import ParsedDocument, ParsedPage


def _settings() -> Settings:
    return Settings(
        extraction_provider="openai",
        llm_api_key="test-key",
        llm_base_url="https://example.test/v1",
        llm_timeout_seconds=1,
        llm_max_retries=0,
    )


def test_malformed_llm_json(monkeypatch) -> None:
    provider = OpenAICompatibleProvider(_settings())

    def fake_post(*_args, **_kwargs):
        request = httpx.Request("POST", "https://example.test/v1/chat/completions")
        return httpx.Response(200, request=request, json={"choices": [{"message": {"content": "not-json"}}]})

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    try:
        provider.extract(
            ParsedDocument(page_count=1, pages=[ParsedPage(page_number=1, text="Tenant: A")]),
            "hash",
            "file.pdf",
        )
        raise AssertionError("expected malformed response to fail")
    except AppError as exc:
        assert exc.code == "LLM_MALFORMED_RESPONSE"


def test_valid_llm_schema_is_accepted(monkeypatch) -> None:
    provider = OpenAICompatibleProvider(_settings())
    content = {
        "tenant_name": {
            "value": "A",
            "page_number": 1,
            "source_text": "Tenant: A",
            "confidence_status": "evidence_found",
        },
        "landlord_name": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "property_address": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "commencement_date": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "expiration_date": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "monthly_base_rent": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "currency": {"value": None, "page_number": None, "source_text": None, "confidence_status": "missing"},
        "renewal_notice_days": {
            "value": None,
            "page_number": None,
            "source_text": None,
            "confidence_status": "missing",
        },
    }

    def fake_post(*_args, **_kwargs):
        request = httpx.Request("POST", "https://example.test/v1/chat/completions")
        return httpx.Response(
            200,
            request=request,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    result = provider.extract(
        ParsedDocument(page_count=1, pages=[ParsedPage(page_number=1, text="Tenant: A")]),
        "hash",
        "file.pdf",
    )
    assert result.tenant_name.value == "A"
