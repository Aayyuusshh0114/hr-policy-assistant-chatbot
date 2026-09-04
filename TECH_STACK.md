# Technology stack

This document explains each major technology in the HR Policy Assistant, why it was selected, and where it is used.

## Stack at a glance

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | HTML5, CSS3, vanilla JavaScript | Responsive upload, document management, provider selection, chat, and citations |
| API | FastAPI, Uvicorn | Typed HTTP endpoints, validation, lifecycle management, and static-file serving |
| Data models | Pydantic, pydantic-settings | API schemas and environment-based configuration |
| Document processing | pypdf | Text and page metadata extraction from text-based PDFs |
| Embeddings | sentence-transformers, MPNet | Local semantic vector generation for policy chunks and questions |
| Vector search | FAISS, NumPy | Persistent cosine-similarity retrieval over document chunks |
| Application data | SQLite | Documents, chunks, conversations, messages, and citations |
| Generation | Groq SDK, Google Gen AI SDK | Interchangeable grounded-answer providers behind one interface |
| Testing and quality | pytest, Ruff | Unit/integration tests, linting, and formatting checks |
| Packaging | pyproject.toml, Docker | Reproducible Python installation and container execution |
| Automation | GitHub Actions | Python 3.12 lint and test checks on pushes and pull requests |

## Why these choices

### FastAPI

FastAPI provides typed request validation, generated OpenAPI documentation, dependency injection, and a clean router model. It is a strong fit for an API-first Python MVP and keeps business logic outside route handlers.

### MPNet and FAISS

`sentence-transformers/all-mpnet-base-v2` produces semantic embeddings locally. FAISS provides fast similarity search without requiring a hosted vector database. This combination keeps the retrieval layer private and inexpensive for a small corpus. The tradeoff is single-machine storage and limited horizontal scaling.

### SQLite

SQLite gives the MVP durable relational state with no separate database service. It is appropriate for a local, single-user demonstration. PostgreSQL would be the expected migration for concurrent or hosted use.

### Groq and Gemini

Both providers implement the same internal interface and live in separate adapter modules. Provider choice therefore does not change ingestion, retrieval, evidence validation, or API response schemas.

### Vanilla frontend

The interface intentionally uses HTML, CSS, and JavaScript without a build pipeline. This reduces setup and keeps the portfolio project easy to inspect. A component framework would become useful if the interface expanded to authentication, administration, analytics, or complex state.

## Request lifecycle

1. A PDF is validated, stored, and parsed page by page.
2. Extracted text is chunked with source metadata.
3. MPNet converts chunks into normalized vectors.
4. FAISS stores vectors while SQLite stores their document and page relationships.
5. A question is embedded and the most relevant chunks are retrieved.
6. Groq or Gemini receives only the question and retrieved excerpts.
7. The service validates the model's cited chunk identifiers before returning the answer and page citations.

## Upgrade path

For production deployment, the main upgrades would be authentication and document ownership, PostgreSQL, object storage, background ingestion workers, OCR, hybrid retrieval and reranking, observability, rate limiting, and provider/privacy approval.
