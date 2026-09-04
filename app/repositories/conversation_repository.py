from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.repositories.database import Database
from app.schemas.conversation import (
    CitationResponse,
    ConversationDetail,
    ConversationResponse,
    MessageResponse,
)
from app.schemas.retrieval import SearchResult


class ConversationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database = Database(database_path)
        self.database.initialize()

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def create(self, title: str) -> ConversationResponse:
        conversation_id = str(uuid4())
        now = self._now()
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conversation_id, title.strip(), now, now),
            )
        return ConversationResponse(
            id=conversation_id,
            title=title.strip(),
            created_at=now,
            updated_at=now,
        )

    def list(self) -> list[ConversationResponse]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [ConversationResponse.model_validate(dict(row)) for row in rows]

    def exists(self, conversation_id: str) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        return row is not None

    def messages(self, conversation_id: str, limit: int | None = None) -> list[MessageResponse]:
        query = "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at"
        parameters: list[object] = [conversation_id]
        if limit is not None:
            query = """
                SELECT * FROM (
                    SELECT * FROM messages WHERE conversation_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ) ORDER BY created_at
            """
            parameters.append(limit)
        with self.database.connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
            result = []
            for row in rows:
                citations = connection.execute(
                    """
                    SELECT c.chunk_id, c.document_id, d.original_filename AS filename,
                           c.page_number, c.excerpt
                    FROM citations c JOIN documents d ON d.id = c.document_id
                    WHERE c.message_id = ? ORDER BY c.rowid
                    """,
                    (row["id"],),
                ).fetchall()
                data = dict(row)
                data["citations"] = [CitationResponse.model_validate(dict(c)) for c in citations]
                result.append(MessageResponse.model_validate(data))
        return result

    def get(self, conversation_id: str) -> ConversationDetail | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
        if not row:
            return None
        return ConversationDetail(**dict(row), messages=self.messages(conversation_id))

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        provider: str | None = None,
        standalone_question: str | None = None,
        citations: list[SearchResult] | None = None,
    ) -> MessageResponse:
        message_id = str(uuid4())
        now = self._now()
        citations = citations or []
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO messages
                    (id, conversation_id, role, content, provider, standalone_question, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (message_id, conversation_id, role, content, provider, standalone_question, now),
            )
            connection.executemany(
                """
                INSERT INTO citations
                    (id, message_id, chunk_id, document_id, page_number, excerpt)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid4()),
                        message_id,
                        c.chunk_id,
                        c.document_id,
                        c.page_number,
                        c.text[:500],
                    )
                    for c in citations
                ],
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id)
            )
        return self.messages(conversation_id, limit=1)[0]

    def delete(self, conversation_id: str) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
        return cursor.rowcount > 0
