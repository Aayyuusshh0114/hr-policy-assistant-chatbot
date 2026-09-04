from datetime import UTC, datetime
from pathlib import Path

from app.repositories.database import Database
from app.schemas.retrieval import IndexStatus


class IndexRepository:
    def __init__(self, database_path: Path) -> None:
        self.database = Database(database_path)
        self.database.initialize()

    def record_rebuild(self, vector_count: int, embedding_model: str) -> IndexStatus:
        now = datetime.now(UTC).isoformat()
        with self.database.connect() as connection:
            current = connection.execute(
                "SELECT version FROM index_state WHERE id = 1"
            ).fetchone()
            version = int(current["version"]) + 1 if current else 1
            connection.execute(
                """
                INSERT INTO index_state (id, version, vector_count, embedding_model, updated_at)
                VALUES (1, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    version = excluded.version,
                    vector_count = excluded.vector_count,
                    embedding_model = excluded.embedding_model,
                    updated_at = excluded.updated_at
                """,
                (version, vector_count, embedding_model, now),
            )
        return IndexStatus(
            version=version,
            vector_count=vector_count,
            embedding_model=embedding_model,
            updated_at=now,
        )

    def get_status(self) -> IndexStatus | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM index_state WHERE id = 1").fetchone()
        return IndexStatus.model_validate(dict(row)) if row else None

