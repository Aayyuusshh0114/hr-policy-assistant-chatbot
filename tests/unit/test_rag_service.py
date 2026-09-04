import json
from pathlib import Path

from app.core.config import Settings
from app.prompts.answer_prompt import build_answer_prompt
from app.prompts.guardrails import SYSTEM_GUARDRAILS
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.database import Database
from app.schemas.retrieval import SearchResult
from app.services.rag_service import REFUSAL, RagService


class StubProvider:
    name = "stub"
    model_name = "stub-model"

    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    def complete(self, _messages) -> str:
        return next(self.responses)


class StubIndex:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results
        self.queries: list[str] = []

    def search(self, query: str, _k: int, _threshold: float | None):
        self.queries.append(query)
        return self.results


def repository(tmp_path: Path) -> ConversationRepository:
    path = tmp_path / "rag.db"
    Database(path).initialize()
    return ConversationRepository(path)


def test_no_retrieval_evidence_returns_refusal(tmp_path: Path) -> None:
    conversations = repository(tmp_path)
    conversation = conversations.create("Test")
    service = RagService(Settings(_env_file=None), conversations, StubIndex([]), StubProvider([]))

    response = service.ask(conversation.id, "Is gym membership included?")

    assert response.insufficient_evidence is True
    assert response.message.content == REFUSAL
    assert response.message.citations == []


def test_answer_uses_only_declared_retrieved_citation(tmp_path: Path) -> None:
    conversations = repository(tmp_path)
    conversation = conversations.create("Leave")
    match = SearchResult(
        chunk_id="chunk-1",
        document_id="document-1",
        filename="Leave Policy.pdf",
        page_number=2,
        chunk_index=0,
        text="Employees receive 21 paid leave days.",
        score=0.9,
    )
    # Citation foreign keys require matching persisted source records.
    with conversations.database.connect() as connection:
        now = "2026-09-03T00:00:00+00:00"
        connection.execute(
            """INSERT INTO documents
            (id, original_filename, stored_filename, content_hash, mime_type, size_bytes,
             page_count, chunk_count, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "document-1", "Leave Policy.pdf", "document-1.pdf", "hash", "application/pdf",
                100, 2, 1, "ready", now, now,
            ),
        )
        connection.execute(
            """INSERT INTO chunks
            (id, document_id, page_number, chunk_index, text, vector_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("chunk-1", "document-1", 2, 0, match.text, 1, now),
        )
    provider = StubProvider(
        [
            json.dumps(
                {
                    "answer": "Employees receive 21 paid leave days.",
                    "used_chunk_ids": ["chunk-1"],
                }
            )
        ]
    )
    service = RagService(Settings(_env_file=None), conversations, StubIndex([match]), provider)

    response = service.ask(conversation.id, "How much paid leave is available?")

    assert response.insufficient_evidence is False
    assert response.message.citations[0].filename == "Leave Policy.pdf"
    assert response.message.citations[0].page_number == 2


def test_follow_up_is_rewritten_before_retrieval(tmp_path: Path) -> None:
    conversations = repository(tmp_path)
    conversation = conversations.create("Referral")
    conversations.add_message(conversation.id, "user", "What is the referral policy?")
    conversations.add_message(conversation.id, "assistant", "It rewards eligible referrals.")
    index = StubIndex([])
    provider = StubProvider(["Who is eligible for the employee referral policy?"])

    RagService(Settings(_env_file=None), conversations, index, provider).ask(
        conversation.id, "Who is eligible for it?"
    )

    assert index.queries == ["Who is eligible for the employee referral policy?"]


def test_prompts_define_a_professional_grounded_answer_contract() -> None:
    prompt = build_answer_prompt("When is payroll?", "CHUNK_ID: one\nTEXT: Friday")

    assert "Give the conclusion first" in prompt
    assert "Do not infer" in prompt
    assert "If policies conflict" in prompt
    assert "calm, neutral, businesslike tone" in SYSTEM_GUARDRAILS
    assert "under 150 words" in SYSTEM_GUARDRAILS
