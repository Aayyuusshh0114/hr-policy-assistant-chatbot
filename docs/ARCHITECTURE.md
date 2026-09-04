# Architecture

The application follows a layered, provider-agnostic structure. HTTP routes coordinate requests; services own use cases; repositories own persistence; infrastructure adapters isolate PDFs, embeddings, FAISS, and external LLM SDKs.

```text
Browser
  -> app/api/routes             HTTP boundary
  -> app/services               ingestion, retrieval, and RAG use cases
  -> app/repositories           SQLite persistence
  -> app/document_processing    PDF validation, extraction, and chunking
  -> app/embeddings             local embedding interface and worker
  -> app/vectorstores           persistent FAISS adapter
  -> app/llms                   Groq/Gemini provider adapters
  -> app/prompts                grounding and response contracts
```

## Directory responsibilities

| Path | Responsibility |
|---|---|
| `app/api` | Version-neutral route composition and dependency wiring |
| `app/core` | Configuration, logging, and application exceptions |
| `app/schemas` | Validated request and response contracts |
| `app/services` | Business workflows with no frontend concerns |
| `app/repositories` | SQL and persistence boundaries |
| `app/document_processing` | File validation, parsing, and chunking |
| `app/embeddings` | Embedding abstraction and MPNet implementation |
| `app/vectorstores` | Vector-index persistence and similarity search |
| `app/llms` | Common provider contract plus isolated vendor adapters |
| `app/prompts` | Versionable retrieval and answer instructions |
| `frontend` | Framework-free browser client |
| `tests` | Unit, integration, UI-contract, PDF, and evaluation assets |
| `data` | Git-ignored runtime uploads, database, and FAISS files |
| `docs` | Architecture, security, decisions, status, and demo guidance |

## Design boundaries

- Routes do not contain retrieval, prompt, or database implementation logic.
- Services depend on stable interfaces rather than Groq or Gemini directly.
- Retrieved chunk IDs are validated server-side before citations are persisted.
- Runtime documents and indexes are not committed to source control.
- The current deployment boundary is deliberately local and single-user.

This is professional MVP architecture, not a claim of production readiness. A shared deployment still needs identity, authorization, tenant-scoped retrieval, background jobs, monitoring, backups, and privacy controls.
