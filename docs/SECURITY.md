# Security and deployment boundary

The current MVP is designed for one trusted user on localhost. It has no authentication or policy-level authorization and must not be exposed to a network or public URL.

Before employee-facing deployment:

1. Obtain written approval for sending policy excerpts and employee questions to each configured LLM vendor.
2. Add SSO, user identity, workspace isolation, and document-level authorization.
3. Replace `.env` secrets with deployment-managed secrets.
4. Add HTTPS, rate limits, request limits, audit logs, retention controls, and backups.
5. Run adversarial testing against prompt injection, malicious PDFs, cross-user leakage, and unsupported-answer behavior.
6. Establish an HR escalation and correction workflow.

The application validates uploads, generates server-side filenames, limits upload size, does not expose raw exceptions, restricts CORS, and treats retrieved text as untrusted data. These controls reduce risk but do not replace production identity and governance.

