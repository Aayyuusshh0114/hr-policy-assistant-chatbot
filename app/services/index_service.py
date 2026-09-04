from threading import RLock

import numpy as np

from app.embeddings.base import EmbeddingModel
from app.repositories.document_repository import DocumentRepository
from app.repositories.index_repository import IndexRepository
from app.schemas.retrieval import IndexStatus, SearchResult
from app.vectorstores.faiss_store import FaissStore


class IndexService:
    def __init__(
        self,
        documents: DocumentRepository,
        index_repository: IndexRepository,
        embeddings: EmbeddingModel,
        store: FaissStore,
    ) -> None:
        self.documents = documents
        self.index_repository = index_repository
        self.embeddings = embeddings
        self.store = store
        self._rebuild_lock = RLock()

    def rebuild(self) -> IndexStatus:
        with self._rebuild_lock:
            chunks = self.documents.list_indexable_chunks()
            if chunks:
                vectors = self.embeddings.embed_documents([chunk.text for chunk in chunks])
                vector_ids = np.arange(1, len(chunks) + 1, dtype=np.int64)
                assignments = {
                    chunk.id: int(vector_id)
                    for chunk, vector_id in zip(chunks, vector_ids, strict=True)
                }
            else:
                vectors = np.empty((0, 0), dtype=np.float32)
                vector_ids = np.empty((0,), dtype=np.int64)
                assignments = {}

            self.store.replace(vectors, vector_ids)
            self.documents.replace_vector_ids(assignments)
            return self.index_repository.record_rebuild(
                vector_count=len(chunks),
                embedding_model=self.embeddings.model_name,
            )

    def search(self, query: str, k: int, score_threshold: float | None) -> list[SearchResult]:
        index_status = self.index_repository.get_status()
        if index_status and index_status.embedding_model != self.embeddings.model_name:
            raise ValueError("The configured embedding model differs from the indexed model.")
        query_vector = self.embeddings.embed_query(query)
        matches = self.store.search(query_vector, k)
        if score_threshold is not None:
            matches = [
                (vector_id, score)
                for vector_id, score in matches
                if score >= score_threshold
            ]

        chunks = self.documents.get_ready_chunks_by_vector_ids(
            [vector_id for vector_id, _ in matches]
        )
        return [
            SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                filename=chunk.original_filename,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=score,
            )
            for vector_id, score in matches
            if (chunk := chunks.get(vector_id)) is not None
        ]
