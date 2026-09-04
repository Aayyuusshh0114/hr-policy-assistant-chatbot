from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.embeddings.huggingface import HuggingFaceEmbeddingModel
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.index_repository import IndexRepository
from app.services.index_service import IndexService
from app.services.ingestion_service import IngestionService
from app.vectorstores.faiss_store import FaissStore


def get_document_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentRepository:
    return DocumentRepository(settings.resolved_database_path)


def get_conversation_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ConversationRepository:
    return ConversationRepository(settings.resolved_database_path)


def get_index_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IndexRepository:
    return IndexRepository(settings.resolved_database_path)


@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddingModel:
    settings = get_settings()
    return HuggingFaceEmbeddingModel(
        settings.embedding_model,
        settings.embedding_batch_size,
        settings.embedding_local_files_only,
        settings.embedding_device,
        settings.embedding_subprocess,
    )


@lru_cache
def get_faiss_store() -> FaissStore:
    return FaissStore(get_settings().resolved_faiss_index_directory)


def get_index_service(
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    index_repository: Annotated[IndexRepository, Depends(get_index_repository)],
    embeddings: Annotated[HuggingFaceEmbeddingModel, Depends(get_embedding_model)],
    store: Annotated[FaissStore, Depends(get_faiss_store)],
) -> IndexService:
    return IndexService(
        documents=repository,
        index_repository=index_repository,
        embeddings=embeddings,
        store=store,
    )


def get_ingestion_service(
    settings: Annotated[Settings, Depends(get_settings)],
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
    index_service: Annotated[IndexService, Depends(get_index_service)],
) -> IngestionService:
    return IngestionService(settings, repository, index_service)
