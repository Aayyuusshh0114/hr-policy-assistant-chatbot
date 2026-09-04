# HR Assistant Decision Log

This log records product and architecture decisions that affect implementation. Changes should be added as new dated entries rather than silently changing assumptions.

| ID | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| AD-01 | 2026-09-03 | Use FastAPI for the backend. | Typed validation, file upload support, generated API documentation, and maintainable service boundaries. | Accepted |
| AD-02 | 2026-09-03 | Build a modular monolith for version 1. | The application is too small to justify distributed services. | Accepted |
| AD-03 | 2026-09-03 | Use FAISS for vectors and SQLite for application metadata. | FAISS does not manage document lifecycle, conversations, or relational metadata. | Accepted |
| AD-04 | 2026-09-03 | Support text PDFs only in version 1. | OCR introduces a separate accuracy and operational problem. | Accepted |
| AD-05 | 2026-09-03 | Keep Groq and Gemini behind one provider interface. | Prevents duplicated RAG logic and allows consistent testing. | Accepted |
| AD-06 | 2026-09-03 | Make providers explicitly selectable; do not silently fall back. | Predictable behavior is more valuable than hidden resilience during evaluation. | Accepted |
| AD-07 | 2026-09-03 | Persist conversations per conversation ID. | Eliminates global history leakage and supports correct follow-ups. | Accepted |
| AD-08 | 2026-09-03 | Keep version 1 localhost-only and single-user. | Authentication and authorization are not yet implemented. | Accepted |
| AD-09 | 2026-09-03 | Use generated storage names and content hashes for uploads. | Prevents unsafe paths and supports duplicate detection. | Accepted |
| AD-10 | 2026-09-03 | Treat notebook evaluation as a smoke test. | Eight questions cannot establish production retrieval or answer quality. | Accepted |

## Pending decisions before production deployment

| ID | Decision needed | Owner |
|---|---|---|
| PD-01 | Approve whether company policy text and employee questions may be processed by Groq, Gemini, or both. | Security/Legal/HR |
| PD-02 | Select authentication and SSO mechanism. | Engineering/IT |
| PD-03 | Define document and conversation retention periods. | HR/Legal |
| PD-04 | Define user roles and policy-level access controls. | HR/IT |
| PD-05 | Define human escalation and correction workflow. | HR |
| PD-06 | Select deployment environment, regional requirements, and production data stores. | Engineering/IT |
