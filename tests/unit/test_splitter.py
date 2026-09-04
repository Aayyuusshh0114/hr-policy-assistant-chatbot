import pytest

from app.document_processing.splitter import TextSplitter


def test_short_text_remains_one_chunk() -> None:
    splitter = TextSplitter(chunk_size=100, chunk_overlap=20)

    assert splitter.split_text("A short policy statement.") == ["A short policy statement."]


def test_long_text_is_split_with_bounded_chunks() -> None:
    splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
    chunks = splitter.split_text("Sentence about leave policy. " * 20)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 100 for chunk in chunks)


def test_invalid_overlap_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid chunk"):
        TextSplitter(chunk_size=100, chunk_overlap=100)

