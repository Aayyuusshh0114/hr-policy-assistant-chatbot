from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.1.0"


def test_readiness_reports_unimplemented_capabilities() -> None:
    with TestClient(app) as client:
        response = client.get("/api/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["capabilities"] == {
        "document_ingestion": True,
        "vector_search": True,
        "chat": True,
    }
    assert all(body["runtime_directories"].values())


def test_frontend_is_served() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "HR Policy Assistant" in response.text
