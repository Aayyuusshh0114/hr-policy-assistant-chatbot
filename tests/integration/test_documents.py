from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.api.dependencies import (
    get_document_repository,
    get_index_repository,
    get_index_service,
    get_ingestion_service,
)
from app.core.config import Settings
from app.main import app
from app.repositories.database import Database
from app.repositories.document_repository import DocumentRepository
from app.repositories.index_repository import IndexRepository
from app.services.index_service import IndexService
from app.services.ingestion_service import IngestionService
from app.vectorstores.faiss_store import FaissStore
from tests.fakes import FakeEmbeddingModel


@pytest.fixture
def document_client(tmp_path: Path):
    settings = Settings(
        _env_file=None,
        app_env="test",
        upload_directory=tmp_path / "uploads",
        faiss_index_directory=tmp_path / "indexes",
        database_path=tmp_path / "database" / "test.db",
    )
    settings.ensure_runtime_directories()
    Database(settings.resolved_database_path).initialize()
    repository = DocumentRepository(settings.resolved_database_path)
    index_service = IndexService(
        repository,
        IndexRepository(settings.resolved_database_path),
        FakeEmbeddingModel(),
        FaissStore(settings.resolved_faiss_index_directory),
    )
    service = IngestionService(settings, repository, index_service)
    app.dependency_overrides[get_document_repository] = lambda: repository
    app.dependency_overrides[get_index_repository] = lambda: index_service.index_repository
    app.dependency_overrides[get_index_service] = lambda: index_service
    app.dependency_overrides[get_ingestion_service] = lambda: service

    with TestClient(app) as client:
        yield client, repository

    app.dependency_overrides.clear()


def make_text_pdf() -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_reference})}
    )
    content = DecodedStreamObject()
    content.set_data(
        b"BT /F1 12 Tf 72 720 Td "
        b"(Employees receive 21 days of paid leave each year.) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(content)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def make_blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_rejects_non_pdf_signature(document_client) -> None:
    client, _ = document_client
    response = client.post(
        "/api/documents",
        files={"file": ("policy.pdf", b"not really a PDF", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "The uploaded file is not a valid PDF."


def test_blank_pdf_is_recorded_as_failed(document_client) -> None:
    client, _ = document_client
    response = client.post(
        "/api/documents",
        files={"file": ("blank.pdf", make_blank_pdf(), "application/pdf")},
    )

    assert response.status_code == 202
    document_id = response.json()["document"]["id"]
    status_response = client.get(f"/api/documents/{document_id}")
    assert status_response.json()["status"] == "failed"
    assert "OCR" in status_response.json()["error_message"]


def test_duplicate_pdf_is_rejected(document_client) -> None:
    client, _ = document_client
    pdf = make_blank_pdf()
    first = client.post(
        "/api/documents",
        files={"file": ("first.pdf", pdf, "application/pdf")},
    )
    second = client.post(
        "/api/documents",
        files={"file": ("second.pdf", pdf, "application/pdf")},
    )

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json()["detail"]["document_id"] == first.json()["document"]["id"]


def test_document_can_be_listed_and_deleted(document_client) -> None:
    client, _ = document_client
    response = client.post(
        "/api/documents",
        files={"file": ("blank.pdf", make_blank_pdf(), "application/pdf")},
    )
    document_id = response.json()["document"]["id"]

    listed = client.get("/api/documents")
    assert listed.json()["total"] == 1
    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    assert client.get(f"/api/documents/{document_id}").status_code == 404


def test_text_pdf_reaches_ready_and_persists_chunks(document_client) -> None:
    client, repository = document_client
    response = client.post(
        "/api/documents",
        files={"file": ("leave-policy.pdf", make_text_pdf(), "application/pdf")},
    )

    assert response.status_code == 202
    document_id = response.json()["document"]["id"]
    persisted = repository.get_document(document_id)
    assert persisted is not None
    assert persisted.status == "ready"
    assert persisted.page_count == 1
    assert persisted.chunk_count == 1
    assert persisted.error_message is None

    search = client.post("/api/search", json={"query": "paid leave days"})
    assert search.status_code == 200
    assert search.json()["total"] == 1
    assert search.json()["results"][0]["filename"] == "leave-policy.pdf"
    assert search.json()["results"][0]["page_number"] == 1

    assert client.delete(f"/api/documents/{document_id}").status_code == 204
    search_after_delete = client.post("/api/search", json={"query": "paid leave days"})
    assert search_after_delete.json()["total"] == 0
    assert client.get("/api/search/index").json()["vector_count"] == 0
