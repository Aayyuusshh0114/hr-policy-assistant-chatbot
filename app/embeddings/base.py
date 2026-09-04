from typing import Protocol

import numpy as np
from numpy.typing import NDArray


class EmbeddingModel(Protocol):
    @property
    def model_name(self) -> str: ...

    def embed_documents(self, texts: list[str]) -> NDArray[np.float32]: ...

    def embed_query(self, text: str) -> NDArray[np.float32]: ...

