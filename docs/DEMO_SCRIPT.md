# 90-second portfolio demo

Use only the synthetic PDFs in `output/pdf/` when recording or sharing the application.

1. Start on the empty workspace and briefly show the Groq/Gemini selector.
2. Upload all four demo policies. Point out the page and chunk counts after indexing.
3. Ask: "How many paid leave days are available?" Open the source citation.
4. Ask: "What notice period applies to Level 3?" Show that the answer comes from a different document.
5. Ask a follow-up: "Can that be waived?" This demonstrates conversation-aware retrieval.
6. Switch provider and explain that both providers use the same retrieval and citation pipeline.
7. End on the architecture and safety message: answers are restricted to retrieved evidence.

Do not upload real employee records or confidential company policies to a portfolio demo. External LLM providers receive the retrieved excerpts and question.

Suggested LinkedIn caption:

> Built an evidence-grounded HR Policy Assistant with FastAPI, FAISS, MPNet embeddings, Groq/Gemini, and a responsive vanilla JavaScript UI. It supports PDF ingestion, persistent vector search, conversational follow-ups, and verifiable page citations. I also added synthetic policy documents and a labelled retrieval evaluation set so the demo is reproducible without exposing company data.
