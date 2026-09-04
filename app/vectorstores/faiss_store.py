import os
from pathlib import Path
from threading import RLock

import numpy as np
from numpy.typing import NDArray


class FaissStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.index_path = directory / "hr_policies.faiss"
        self._index = None
        self._lock = RLock()

    def _load(self):
        if self._index is None and self.index_path.exists():
            import faiss

            self._index = faiss.read_index(str(self.index_path))
        return self._index

    def replace(self, vectors: NDArray[np.float32], vector_ids: NDArray[np.int64]) -> None:
        if vectors.ndim != 2 or len(vectors) != len(vector_ids):
            raise ValueError("Vectors and vector IDs must have matching two-dimensional data.")

        with self._lock:
            import faiss

            self.directory.mkdir(parents=True, exist_ok=True)
            if len(vectors) == 0:
                self.index_path.unlink(missing_ok=True)
                self._index = None
                return

            normalized = np.ascontiguousarray(vectors, dtype=np.float32)
            faiss.normalize_L2(normalized)
            base_index = faiss.IndexFlatIP(normalized.shape[1])
            index = faiss.IndexIDMap2(base_index)
            index.add_with_ids(normalized, np.ascontiguousarray(vector_ids, dtype=np.int64))

            temporary_path = self.index_path.with_suffix(".tmp")
            faiss.write_index(index, str(temporary_path))
            os.replace(temporary_path, self.index_path)
            self._index = index

    def search(self, query_vector: NDArray[np.float32], k: int) -> list[tuple[int, float]]:
        with self._lock:
            index = self._load()
            if index is None or index.ntotal == 0:
                return []
            import faiss

            query = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
            if query.shape[1] != index.d:
                raise ValueError(
                    "Query embedding dimensions do not match the persisted FAISS index."
                )
            faiss.normalize_L2(query)
            scores, ids = index.search(query, min(k, index.ntotal))
            return [
                (int(vector_id), float(score))
                for vector_id, score in zip(ids[0], scores[0], strict=True)
                if vector_id >= 0
            ]
