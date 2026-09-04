from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "HR Policy Assistant"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    allowed_origins: str = "http://127.0.0.1:8000,http://localhost:8000"

    llm_provider: Literal["groq", "gemini"] = "groq"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    embedding_batch_size: int = Field(default=32, ge=1, le=256)
    embedding_local_files_only: bool = True
    embedding_device: str = "cpu"
    embedding_subprocess: bool = True
    upload_directory: Path = Path("data/uploads")
    faiss_index_directory: Path = Path("data/indexes")
    database_path: Path = Path("data/database/hr_assistant.db")
    frontend_directory: Path = Path("frontend")

    max_upload_size_mb: int = Field(default=20, ge=1, le=200)
    chunk_size: int = Field(default=800, ge=100, le=5000)
    chunk_overlap: int = Field(default=150, ge=0, le=2000)
    retrieval_k: int = Field(default=5, ge=1, le=50)
    retrieval_fetch_k: int = Field(default=15, ge=1, le=100)
    retrieval_score_threshold: float | None = Field(default=0.25, ge=0)
    max_history_messages: int = Field(default=6, ge=0, le=20)

    @field_validator("retrieval_score_threshold", mode="before")
    @classmethod
    def empty_threshold_uses_safe_default(cls, value: object) -> object:
        return 0.25 if value == "" else value

    @field_validator("gemini_model", mode="before")
    @classmethod
    def empty_gemini_model_uses_default(cls, value: object) -> object:
        return "gemini-2.5-flash" if value == "" else value

    @model_validator(mode="after")
    def validate_related_values(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.retrieval_fetch_k < self.retrieval_k:
            raise ValueError("RETRIEVAL_FETCH_K must be greater than or equal to RETRIEVAL_K")
        return self

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    def _resolve_project_path(self, path: Path) -> Path:
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def resolved_upload_directory(self) -> Path:
        return self._resolve_project_path(self.upload_directory)

    @property
    def resolved_faiss_index_directory(self) -> Path:
        return self._resolve_project_path(self.faiss_index_directory)

    @property
    def resolved_database_path(self) -> Path:
        return self._resolve_project_path(self.database_path)

    @property
    def resolved_frontend_directory(self) -> Path:
        return self._resolve_project_path(self.frontend_directory)

    def ensure_runtime_directories(self) -> None:
        self.resolved_upload_directory.mkdir(parents=True, exist_ok=True)
        self.resolved_faiss_index_directory.mkdir(parents=True, exist_ok=True)
        self.resolved_database_path.parent.mkdir(parents=True, exist_ok=True)

    def runtime_directory_status(self) -> dict[str, bool]:
        return {
            "uploads": self.resolved_upload_directory.is_dir(),
            "indexes": self.resolved_faiss_index_directory.is_dir(),
            "database_parent": self.resolved_database_path.parent.is_dir(),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
