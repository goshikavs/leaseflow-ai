from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    service: str
    extraction_provider: str


class ReadyResponse(BaseModel):
    status: str
    database: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
