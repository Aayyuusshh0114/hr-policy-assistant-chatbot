from pathlib import Path

from fastapi.testclient import TestClient

from app.api.dependencies import get_conversation_repository
from app.core.config import get_settings
from app.main import app
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.database import Database


def test_conversation_lifecycle_and_unconfigured_provider(tmp_path: Path) -> None:
    database_path = tmp_path / "conversations.db"
    Database(database_path).initialize()
    repository = ConversationRepository(database_path)
    app.dependency_overrides[get_conversation_repository] = lambda: repository

    try:
        with TestClient(app) as client:
            created = client.post("/api/conversations", json={"title": "Leave questions"})
            assert created.status_code == 201
            conversation_id = created.json()["id"]

            listed = client.get("/api/conversations")
            assert listed.json()["total"] == 1

            detail = client.get(f"/api/conversations/{conversation_id}")
            assert detail.json()["messages"] == []

            settings = get_settings()
            provider = "gemini" if not settings.gemini_api_key else "groq"
            if provider == "groq" and settings.groq_api_key:
                provider = None
            if provider is not None:
                chat = client.post(
                    "/api/chat",
                    json={
                        "conversation_id": conversation_id,
                        "question": "What is the leave policy?",
                        "provider": provider,
                    },
                )
                assert chat.status_code == 400

            assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
            assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
    finally:
        app.dependency_overrides.clear()

