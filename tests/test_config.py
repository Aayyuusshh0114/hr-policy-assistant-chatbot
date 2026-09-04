from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_relative_paths_resolve_from_project_root() -> None:
    settings = Settings(_env_file=None, upload_directory=Path("data/example-uploads"))

    assert settings.resolved_upload_directory.is_absolute()
    assert settings.resolved_upload_directory.parts[-2:] == ("data", "example-uploads")


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP"):
        Settings(_env_file=None, chunk_size=200, chunk_overlap=200)


def test_fetch_count_cannot_be_smaller_than_result_count() -> None:
    with pytest.raises(ValidationError, match="RETRIEVAL_FETCH_K"):
        Settings(_env_file=None, retrieval_k=10, retrieval_fetch_k=5)


def test_allowed_origins_are_parsed() -> None:
    settings = Settings(
        _env_file=None,
        allowed_origins="http://localhost:8000, http://127.0.0.1:8000",
    )

    assert settings.allowed_origin_list == [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

