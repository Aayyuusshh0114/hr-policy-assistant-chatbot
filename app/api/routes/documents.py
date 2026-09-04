from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_document_repository, get_ingestion_service
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentValidationError,
    DuplicateDocumentError,
)
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentListResponse, DocumentResponse, UploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="A text-based PDF policy document")],
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> UploadResponse:
    try:
        document = await service.accept_upload(file)
    except DocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DuplicateDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": str(exc), "document_id": exc.document_id},
        ) from exc

    background_tasks.add_task(service.process_document, document.id)
    return UploadResponse(document=document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentListResponse:
    documents = repository.list_documents()
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    repository: Annotated[DocumentRepository, Depends(get_document_repository)],
) -> DocumentResponse:
    document = repository.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> None:
    try:
        service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

