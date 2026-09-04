import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.repositories.database import Database
from app.schemas.document import DocumentResponse, DocumentStatus
from app.schemas.retrieval import ChunkRecord


class DocumentRepository:
    def __init__(self, database_path: Path) -> None:
        self.database = Database(database_path)
        self.database.initialize()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _to_document(row: sqlite3.Row) -> DocumentResponse:
        return DocumentResponse.model_validate(dict(row))

    def create_document(
        self,
        *,
        document_id: str,
        original_filename: str,
        stored_filename: str,
        content_hash: str,
        mime_type: str,
        size_bytes: int,
    ) -> DocumentResponse:
        now = self._now()
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, original_filename, stored_filename, content_hash, mime_type,
                    size_bytes, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    original_filename,
                    stored_filename,
                    content_hash,
                    mime_type,
                    size_bytes,
                    DocumentStatus.PROCESSING.value,
                    now,
                    now,
                ),
            )
        document = self.get_document(document_id)
        if document is None:  # pragma: no cover - defensive database check
            raise RuntimeError("Document was not persisted.")
        return document

    def find_by_hash(self, content_hash: str) -> DocumentResponse | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
        return self._to_document(row) if row else None

    def get_document(self, document_id: str) -> DocumentResponse | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return self._to_document(row) if row else None

    def get_stored_filename(self, document_id: str) -> str | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT stored_filename FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        return str(row["stored_filename"]) if row else None

    def list_documents(self) -> list[DocumentResponse]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            ).fetchall()
        return [self._to_document(row) for row in rows]

    def save_chunks(self, document_id: str, pages: list[list[str]]) -> None:
        now = self._now()
        chunk_rows = [
            (str(uuid4()), document_id, page_number, index, text, now)
            for page_number, page_chunks in enumerate(pages, start=1)
            for index, text in enumerate(page_chunks)
        ]
        with self.database.connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, page_number, chunk_index, text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                chunk_rows,
            )
            connection.execute(
                """
                UPDATE documents
                SET page_count = ?, chunk_count = ?, error_message = NULL, updated_at = ?
                WHERE id = ?
                """,
                (
                    len(pages),
                    len(chunk_rows),
                    now,
                    document_id,
                ),
            )

    def mark_ready(self, document_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE documents
                SET status = ?, error_message = NULL, updated_at = ?
                WHERE id = ?
                """,
                (DocumentStatus.READY.value, self._now(), document_id),
            )

    def list_indexable_chunks(self) -> list[ChunkRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT c.id, c.document_id, d.original_filename, c.page_number,
                       c.chunk_index, c.text, c.vector_id
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.status IN ('processing', 'ready')
                ORDER BY d.created_at, c.page_number, c.chunk_index
                """
            ).fetchall()
        return [ChunkRecord.model_validate(dict(row)) for row in rows]

    def get_ready_chunks_by_vector_ids(self, vector_ids: list[int]) -> dict[int, ChunkRecord]:
        if not vector_ids:
            return {}
        placeholders = ",".join("?" for _ in vector_ids)
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT c.id, c.document_id, d.original_filename, c.page_number,
                       c.chunk_index, c.text, c.vector_id
                FROM chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.status = 'ready' AND c.vector_id IN ({placeholders})
                """,
                vector_ids,
            ).fetchall()
        return {int(row["vector_id"]): ChunkRecord.model_validate(dict(row)) for row in rows}

    def replace_vector_ids(self, assignments: dict[str, int]) -> None:
        with self.database.connect() as connection:
            connection.execute("UPDATE chunks SET vector_id = NULL")
            connection.executemany(
                "UPDATE chunks SET vector_id = ? WHERE id = ?",
                [(vector_id, chunk_id) for chunk_id, vector_id in assignments.items()],
            )

    def mark_failed(self, document_id: str, error_message: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE documents
                SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (DocumentStatus.FAILED.value, error_message[:500], self._now(), document_id),
            )

    def delete_document(self, document_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0
