from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.embeddings.huggingface import HuggingFaceEmbeddingModel
from app.repositories.database import Database
from app.repositories.document_repository import DocumentRepository
from app.repositories.index_repository import IndexRepository
from app.services.index_service import IndexService
from app.services.ingestion_service import IngestionService
from app.vectorstores.faiss_store import FaissStore

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.ensure_runtime_directories()
    Database(settings.resolved_database_path).initialize()
    logger.info(
        "application_started",
        extra={"app_env": settings.app_env, "llm_provider": settings.llm_provider},
    )
    _recover_interrupted_documents()
    yield
    logger.info("application_stopped")


def _recover_interrupted_documents() -> None:
    repository = DocumentRepository(settings.resolved_database_path)
    interrupted = [
        document.id for document in repository.list_documents() if document.status == "processing"
    ]
    if not interrupted:
        return

    def recover() -> None:
        index_service = IndexService(
            repository,
            IndexRepository(settings.resolved_database_path),
            HuggingFaceEmbeddingModel(
                settings.embedding_model,
                settings.embedding_batch_size,
                settings.embedding_local_files_only,
                settings.embedding_device,
                settings.embedding_subprocess,
            ),
            FaissStore(settings.resolved_faiss_index_directory),
        )
        ingestion = IngestionService(settings, repository, index_service)
        for document_id in interrupted:
            logger.info("recovering_interrupted_document", extra={"id": document_id})
            ingestion.process_document(document_id)

    Thread(target=recover, name="document-recovery", daemon=True).start()


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Local API for the HR Policy Assistant.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["127.0.0.1", "localhost", "testserver"],
)
app.include_router(api_router, prefix="/api")
app.mount("/static", StaticFiles(directory=settings.resolved_frontend_directory), name="static")


@app.get("/", include_in_schema=False)
async def frontend() -> FileResponse:
    return FileResponse(settings.resolved_frontend_directory / "index.html")


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
    )
    return response
