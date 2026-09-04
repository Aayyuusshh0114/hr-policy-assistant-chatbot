import json
import os
import subprocess
import sys
from threading import Lock

import numpy as np
from numpy.typing import NDArray

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


class HuggingFaceEmbeddingModel:
    def __init__(
        self,
        model_name: str,
        batch_size: int = 32,
        local_files_only: bool = True,
        device: str = "cpu",
        use_subprocess: bool = True,
    ) -> None:
        self._model_name = model_name
        self.batch_size = batch_size
        self.local_files_only = local_files_only
        self.device = device
        self.use_subprocess = use_subprocess
        self._model = None
        self._load_lock = Lock()

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self):
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(
                        self._model_name,
                        local_files_only=self.local_files_only,
                        device=self.device,
                    )
        return self._model

    def embed_documents(self, texts: list[str]) -> NDArray[np.float32]:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        if self.use_subprocess:
            return self._embed_in_subprocess(texts)
        vectors = self._get_model().encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def embed_query(self, text: str) -> NDArray[np.float32]:
        if self.use_subprocess:
            return self._embed_in_subprocess([text])[0]
        vectors = self._get_model().encode(
            [text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors[0], dtype=np.float32)

    def _embed_in_subprocess(self, texts: list[str]) -> NDArray[np.float32]:
        payload = json.dumps(
            {
                "model_name": self._model_name,
                "batch_size": self.batch_size,
                "local_files_only": self.local_files_only,
                "device": self.device,
                "texts": texts,
            }
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "app.embeddings.worker"],
                input=payload,
                text=True,
                capture_output=True,
                check=True,
                timeout=120,
                env={**os.environ, "TOKENIZERS_PARALLELISM": "false"},
            )
            return np.asarray(json.loads(completed.stdout), dtype=np.float32)
        except (subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("Embedding worker failed.") from exc
