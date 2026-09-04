# HR Assistant — Phase 1 Requirements and Scope

Status: Approved baseline for implementation  
Date: 2026-09-03  
Target release: Local MVP (version 1)

## 1. Product goal

Build a locally runnable HR policy assistant that lets an authorized user upload PDF policy documents and ask questions whose answers are grounded only in those documents.

The application must return supporting document and page citations, refuse unsupported questions, keep conversations isolated, and allow either Groq or Gemini to be selected as the answer-generation provider.

## 2. Version 1 users and deployment boundary

Version 1 is a single-user, local-development application run from VS Code.

- It will bind to localhost by default.
- It will not be exposed publicly.
- Authentication and multi-user authorization are not part of the local MVP.
- Public, shared, or employee-facing deployment is explicitly blocked until authentication, authorization, privacy review, and production secret management are implemented.

This boundary is important: without authentication, version 1 is safe only for a trusted user on a trusted machine.

## 3. Version 1 functional scope

### 3.1 Document management

The user can:

- Upload one or more PDF files.
- See whether each file is uploaded, processing, ready, or failed.
- View a list of uploaded documents.
- Delete an uploaded document.
- Re-upload a changed version of a document.

The system must:

- Validate file extension, MIME type, size, and readable PDF structure.
- Reject empty, corrupt, unsupported, and oversized files with clear errors.
- Assign every document an internal UUID.
- Calculate a SHA-256 content hash to detect exact duplicates.
- Preserve filename, page number, document ID, and chunk ID metadata.
- Persist uploaded files, metadata, and the vector index across restarts.
- Remove a deleted document from retrieval results.

Version 1 supports text-based PDFs only. OCR for scanned/image-only PDFs is deferred.

### 3.2 Indexing and retrieval

The system will:

- Extract text page by page.
- Split text into configurable overlapping chunks.
- Generate local Hugging Face sentence-transformer embeddings.
- Store and search embeddings with FAISS.
- Store document, chunk, conversation, and index metadata in SQLite.
- Persist FAISS index files under the application data directory.
- Retrieve only chunks belonging to active documents in the current workspace.
- Apply configurable retrieval limits and a relevance threshold.
- Return insufficient-evidence status when relevant context is not found.

The initial embedding model is `sentence-transformers/all-mpnet-base-v2`. Chunk size, overlap, retrieval count, and threshold remain configuration values and must be selected through evaluation rather than assumed to be optimal.

### 3.3 Chat and conversations

The user can:

- Start a new conversation.
- Ask a question about uploaded HR policies.
- Ask contextual follow-up questions.
- View source citations containing filename, page number, and supporting excerpt.
- Clear or switch conversations.
- Choose Groq or Gemini when both providers are configured.

The system must:

- Assign every conversation a UUID.
- Store history per conversation rather than in global application memory.
- Rewrite ambiguous follow-up questions into standalone retrieval queries.
- Generate answers using only retrieved policy context.
- Refuse questions not supported by that context.
- Avoid presenting retrieved-but-unused documents as citations.
- Return a structured error when the selected LLM provider is unavailable.

Conversation history will persist in SQLite across local application restarts.

### 3.4 LLM providers

Groq and Gemini will be implemented as independent provider adapters behind one common interface.

- The RAG service must not contain provider-specific SDK calls.
- Provider selection will be configurable globally and may be overridden per chat request.
- There will be no automatic fallback in the first MVP; silent fallback would make behavior and evaluation harder to understand.
- If a requested provider is not configured, the API will return a clear configuration error.
- Model names will be supplied through environment variables rather than hard-coded.

### 3.5 User interface

The frontend will use HTML, CSS, and browser JavaScript.

It will provide:

- PDF upload controls and upload progress.
- Document processing status and document deletion.
- A chat interface.
- Conversation reset.
- Provider selection.
- Loading, empty, success, and failure states.
- Expandable citations.

The UI must prevent chat submission until at least one document is ready.

## 4. Explicitly out of scope for version 1

- Public internet deployment
- Multiple users or organizations
- Role-based document permissions
- SSO or employee authentication
- OCR and image extraction
- DOCX, spreadsheet, email, or web-page ingestion
- Cloud vector databases
- Automatic synchronization with Drive or HR systems
- Voice input or output
- Fine-tuning an LLM
- Agentic actions against HR systems
- Automatic legal or employment decisions
- Streaming responses, unless it proves trivial after the core flow is stable

## 5. Architecture decisions

### AD-01: FastAPI instead of Flask

FastAPI is selected for typed request validation, file uploads, generated API documentation, and clearer service boundaries.

### AD-02: Modular monolith

The backend will be one deployable application divided into API, service, provider, persistence, and document-processing modules. Microservices would add operational complexity without helping this MVP.

### AD-03: FAISS plus SQLite

FAISS will store/search vectors. SQLite will be the source of truth for document records, chunk metadata, conversations, messages, processing state, hashes, and index versions. FAISS alone is not sufficient for document lifecycle management.

### AD-04: Filesystem persistence

Uploaded PDFs and FAISS artifacts will be stored in dedicated data directories. The application will never derive storage paths directly from an untrusted filename.

### AD-05: Common LLM interface

Groq and Gemini will implement the same provider contract. Prompt construction, retrieval, conversation handling, and citation handling will remain provider-independent.

### AD-06: Session isolation

No global chat-history list is permitted. Every message and retrieval operation must be associated with a conversation ID.

### AD-07: Evidence-based answers

An answer is successful only when relevant context is available. Citations must point to chunks actually used to support the answer, not merely every chunk returned by FAISS.

### AD-08: Local embedding generation

Embedding generation will remain local for the MVP. Policy chunks will be sent to an external service only when they are included in a Groq or Gemini generation request.

## 6. Data model baseline

### Document

- `id`
- `original_filename`
- `stored_filename`
- `content_hash`
- `mime_type`
- `size_bytes`
- `page_count`
- `status`
- `error_message`
- `created_at`
- `updated_at`

### Chunk

- `id`
- `document_id`
- `page_number`
- `chunk_index`
- `text`
- `vector_id`
- `created_at`

### Conversation

- `id`
- `title`
- `created_at`
- `updated_at`

### Message

- `id`
- `conversation_id`
- `role`
- `content`
- `provider`
- `standalone_question`
- `created_at`

### Citation

- `id`
- `message_id`
- `chunk_id`
- `document_id`
- `page_number`
- `excerpt`

## 7. Document and index lifecycle

### Upload

1. Validate the request and file.
2. Calculate its hash and reject or identify exact duplicates.
3. Create a document record with `processing` status.
4. Store the PDF under a generated filename.
5. Extract pages and chunks.
6. Create embeddings and update FAISS.
7. Persist chunk/vector mappings.
8. Mark the document `ready` only after all artifacts are safely saved.
9. Mark it `failed` and retain a safe diagnostic if processing fails.

### Delete

1. Mark the document unavailable for retrieval.
2. Remove its chunk and citation relationships according to database rules.
3. Rebuild or safely update the FAISS index.
4. Delete its stored file only after metadata/index changes succeed.

Deletion must not leave searchable orphan vectors.

### Replacement

A changed PDF is treated as a new document version. The old version remains active until the new one is completely indexed, after which the user can explicitly replace/delete the old version.

## 8. Security and privacy requirements

Even for the local MVP:

- `.env` must be excluded from version control.
- Only `.env.example` may be committed.
- API keys must never appear in responses or logs.
- Filenames must be sanitized and storage names generated by the server.
- Upload size must be limited.
- Raw stack traces must not be returned to the browser.
- Prompt and document content must be treated as untrusted input.
- The application must not follow instructions contained inside uploaded documents.
- Logs must not contain full document contents or complete employee questions by default.
- CORS must default to the local frontend origin rather than allowing every origin.

Before real company policies are sent to Groq or Gemini, the organization must confirm that external processing is allowed under its privacy, retention, and vendor policies.

## 9. Quality requirements

### Correctness

- No answer may rely on a different conversation's history.
- Unsupported questions must receive a stable refusal response.
- Follow-up questions must retain the correct policy subject.
- Deleted documents must not appear in retrieval or citations.
- Page numbers shown to users must be one-based and traceable to the source PDF.

### Reliability

- Application restart must not lose ready documents or conversations.
- A failed upload must not corrupt the existing index.
- Provider timeouts and failures must return structured errors.

### Performance targets for the local MVP

- API health response: under 500 ms under normal local conditions.
- Retrieval after indexing: under 2 seconds for the expected small policy corpus.
- Chat response: target under 15 seconds, excluding external provider outages.
- Upload endpoint must immediately communicate processing state; long indexing work must not appear as a frozen UI.

These are initial targets, not guarantees, and will be measured on the development machine.

## 10. Evaluation requirements

The evaluation dataset must contain at least 50 labelled questions before the MVP is considered complete, including:

- Direct policy questions
- Paraphrases
- Scenario questions
- Multi-turn pronoun/reference questions
- Unsupported HR questions
- Non-HR questions
- Similar concepts from competing policies
- Typographical errors
- Questions whose answer spans multiple pages
- Prompt-injection attempts in user questions and documents

Metrics:

- Document Hit@1 and Hit@3
- Correct-page Hit@1 and Hit@3
- Citation precision
- Answer faithfulness
- Supported-answer correctness
- Unsupported-question refusal rate
- Follow-up resolution accuracy
- Cross-conversation isolation
- Retrieval and generation latency

The existing eight-question notebook audit is a smoke test only and is not an acceptance test.

## 11. MVP acceptance criteria

Phase 1 defines the MVP as acceptable when all of the following are demonstrated:

1. A new developer can configure and start the application from the README.
2. A valid text PDF can be uploaded, indexed, listed, queried, and deleted.
3. State survives an application restart.
4. Duplicate and invalid documents are handled safely.
5. Groq and Gemini pass the same provider contract tests.
6. The user can select either configured provider.
7. Answers contain verified filename, page, and excerpt citations.
8. Insufficient evidence produces a refusal instead of a guessed answer.
9. Referral-policy follow-ups do not drift into insurance or other policies.
10. Two simultaneous conversations remain isolated.
11. Deleted policy content cannot be retrieved.
12. The labelled evaluation suite meets thresholds agreed before deployment.
13. No secret, raw exception, or unsafe upload path is exposed.
14. The application is accessible only locally unless production security work has been completed.

## 12. Decisions deferred beyond Phase 1

These decisions do not block the local MVP but must be resolved before broader deployment:

- Authentication provider and SSO
- User, team, and document authorization model
- Retention duration for documents and conversations
- Whether employee questions may be retained
- Approved external LLM provider and regional/data-retention requirements
- Background job technology for larger deployments
- Cloud storage and managed database choices
- Backup, disaster recovery, and audit-log requirements
- Human escalation workflow for disputed or sensitive HR answers

## 13. Phase 2 entry criteria

Phase 2 may begin using these assumptions unless the product owner changes them:

- FastAPI backend
- HTML/CSS/JavaScript frontend
- PDF-only ingestion
- FAISS plus SQLite persistence
- Local MPNet embeddings
- Groq and Gemini as selectable provider adapters
- Persistent per-conversation history
- Localhost-only, single-user MVP
- No OCR and no public deployment

