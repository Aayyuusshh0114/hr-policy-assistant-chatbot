import hashlib

import numpy as np
from numpy.typing import NDArray


class FakeEmbeddingModel:
    model_name = "test-hash-embeddings"
    dimensions = 16

    def _embed(self, text: str) -> NDArray[np.float32]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode()).digest()
            vector[int.from_bytes(digest[:2], "big") % self.dimensions] += 1
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    def embed_documents(self, texts: list[str]) -> NDArray[np.float32]:
        return np.asarray([self._embed(text) for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> NDArray[np.float32]:
        return self._embed(text)

