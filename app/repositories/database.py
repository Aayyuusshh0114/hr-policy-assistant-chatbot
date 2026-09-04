import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL UNIQUE,
                    content_hash TEXT NOT NULL UNIQUE,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
                    page_count INTEGER,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL CHECK (status IN ('processing', 'ready', 'failed')),
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL CHECK (page_number > 0),
                    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
                    text TEXT NOT NULL,
                    vector_id INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE (document_id, page_number, chunk_index)
                );

                CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
                CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

                CREATE TABLE IF NOT EXISTS index_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL,
                    vector_count INTEGER NOT NULL,
                    embedding_model TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    provider TEXT,
                    standalone_question TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    chunk_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    excerpt TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_citations_message ON citations(message_id);
                """
            )
