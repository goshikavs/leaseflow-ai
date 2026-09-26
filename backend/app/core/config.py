from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LeaseFlow AI"
    environment: str = "development"
    database_url: str = "sqlite:///./data/leaseflow.db"
    storage_dir: str = "./data/uploads"
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:3000"
    demo_actor: str = "demo-reviewer"
    extraction_provider: str = "fixture"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    llm_max_response_bytes: int = 50_000
    samples_dir: str = Field(default="")

    @field_validator("extraction_provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"fixture", "openai"}:
            raise ValueError("EXTRACTION_PROVIDER must be 'fixture' or 'openai'")
        return normalized

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def resolved_samples_dir(self) -> Path:
        if self.samples_dir:
            return Path(self.samples_dir).resolve()
        backend_dir = Path(__file__).resolve().parents[2]
        return (backend_dir.parent / "samples").resolve()

    @property
    def resolved_storage_dir(self) -> Path:
        path = Path(self.storage_dir)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path.resolve()

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("sqlite:///") and not self.database_url.startswith("sqlite:////"):
            raw_path = self.database_url.replace("sqlite:///", "", 1)
            path = Path(raw_path)
            if not path.is_absolute():
                path = (Path(__file__).resolve().parents[2] / path).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path.as_posix()}"
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.resolved_storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
