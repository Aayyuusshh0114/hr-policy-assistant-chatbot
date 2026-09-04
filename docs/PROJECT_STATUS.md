# Project status

Updated: 2026-09-04

| Phase | Status | Notes |
|---|---|---|
| 1. Requirements | Complete | Scope, decisions, lifecycle, and acceptance criteria documented. |
| 2. Foundation | Complete | FastAPI, configuration, logging, frontend serving, and tests. |
| 3. Ingestion | Complete for local MVP | Text PDFs, validation, extraction, chunking, SQLite, and deletion. |
| 4. Retrieval | Complete for local MVP | Local MPNet adapter, persistent FAISS, rebuild, search, and score threshold. |
| 5. LLM providers | Implemented | Separate Groq and Gemini adapters; live calls require user API keys. |
| 6. RAG/conversations | Implemented and locally tested | Isolated history, rewriting, refusal, and verified chunk citations. |
| 7. Frontend | Implemented | Upload, document state, deletion, provider selection, chat, and citations. |
| 8. Evaluation | Demo framework complete | Automated tests, four synthetic policies, a 24-case labelled set, and evaluation runner exist. |
| 9. Security | Local controls complete; production blocked | No authentication or authorization. Vendor/privacy approval is unresolved. |
| 10. Packaging | Portfolio packaging complete | Architecture, tech stack, demo guide, Docker, and GitHub CI are included. |

## External completion gates

The following cannot be completed responsibly from the current workspace alone:

- Live Groq and Gemini verification requires valid API keys.
- Production retrieval evaluation requires actual approved policy PDFs.
- A production acceptance set requires HR-reviewed expected sources and answers.
- Public deployment requires identity, authorization, privacy approval, retention decisions, and an approved hosting target.
