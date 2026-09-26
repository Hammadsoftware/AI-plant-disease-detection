from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_name: str = "Plant Disease Diagnosis API"
    app_version: str = "2.0.0"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    model_path: Path = Path("models/efficientnet_v2_s_best.torchscript.pt")
    class_labels_path: Path = Path("models/class_labels.json")
    low_confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0)
    max_concurrent_inferences: int = Field(default=1, ge=1, le=32)

    max_upload_size_mb: int = Field(default=10, ge=1, le=100)
    max_image_pixels: int = Field(default=25_000_000, ge=1_000_000)
    min_image_dimension: int = Field(default=32, ge=1)
    max_image_dimension: int = Field(default=10_000, ge=32)
    store_uploads: bool = True
    upload_dir: Path = Path("uploads")
    image_jpeg_quality: int = Field(default=90, ge=60, le=95)

    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_base_url: str = "https://api.groq.com"
    groq_timeout_seconds: float = Field(default=90.0, gt=0.0, le=600.0)
    groq_health_timeout_seconds: float = Field(default=3.0, gt=0.0, le=30.0)
    groq_health_cache_seconds: float = Field(default=30.0, ge=0.0, le=300.0)
    groq_max_tokens: int = Field(default=4096, ge=256, le=8192)
    groq_reasoning_effort: str = "low"
    groq_max_retries: int = Field(default=2, ge=0, le=10)
    groq_max_payload_chars: int = Field(default=12000, ge=1000, le=200000)
    max_concurrent_groq_requests: int = Field(default=2, ge=1, le=16)

    search_provider: Literal["tavily", "disabled"] = "tavily"
    tavily_api_key: SecretStr | None = None
    tavily_base_url: str = "https://api.tavily.com"
    search_timeout_seconds: float = Field(default=20.0, gt=0.0, le=120.0)
    search_max_results_per_query: int = Field(default=5, ge=1, le=10)
    search_max_queries_per_node: int = Field(default=2, ge=1, le=4)
    max_concurrent_search_requests: int = Field(default=6, ge=1, le=64)
    research_country: str = "Pakistan"

    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    cors_allow_credentials: bool = False

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("groq_model", "research_country")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("groq_base_url", "tavily_base_url")
    @classmethod
    def normalize_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith(("http://", "https://")):
            raise ValueError("base URL must use HTTP or HTTPS")
        return value

    def resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()

    @property
    def resolved_model_path(self) -> Path:
        return self.resolve_path(self.model_path)

    @property
    def resolved_class_labels_path(self) -> Path:
        return self.resolve_path(self.class_labels_path)

    @property
    def resolved_upload_dir(self) -> Path:
        return self.resolve_path(self.upload_dir)

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def max_request_size_bytes(self) -> int:
        return self.max_upload_size_bytes + (1024 * 1024)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def tavily_configured(self) -> bool:
        return bool(
            self.search_provider == "tavily"
            and self.tavily_api_key
            and self.tavily_api_key.get_secret_value().strip()
        )

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
