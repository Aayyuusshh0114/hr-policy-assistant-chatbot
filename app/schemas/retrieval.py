from datetime import datetime

from pydantic import BaseModel, Field


class ChunkRecord(BaseModel):
    id: str
    document_id: str
    original_filename: str
    page_number: int
    chunk_index: int
    text: str
    vector_id: int | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    k: int | None = Field(default=None, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class IndexStatus(BaseModel):
    version: int
    vector_count: int
    embedding_model: str
    updated_at: datetime

