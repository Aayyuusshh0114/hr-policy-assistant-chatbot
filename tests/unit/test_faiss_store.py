from pathlib import Path

import numpy as np

from app.vectorstores.faiss_store import FaissStore


def test_index_persists_and_reloads(tmp_path: Path) -> None:
    vectors = np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
    ids = np.asarray([10, 20], dtype=np.int64)
    store = FaissStore(tmp_path)
    store.replace(vectors, ids)

    reloaded = FaissStore(tmp_path)
    assert reloaded.search(np.asarray([0.9, 0.1], dtype=np.float32), 1)[0][0] == 10


def test_empty_rebuild_removes_index(tmp_path: Path) -> None:
    store = FaissStore(tmp_path)
    store.replace(
        np.asarray([[1.0, 0.0]], dtype=np.float32),
        np.asarray([1], dtype=np.int64),
    )
    store.replace(
        np.empty((0, 0), dtype=np.float32),
        np.empty((0,), dtype=np.int64),
    )

    assert not store.index_path.exists()
    assert store.search(np.asarray([1.0, 0.0], dtype=np.float32), 1) == []
