from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_index_repository, get_index_service
from app.core.config import Settings, get_settings
from app.repositories.index_repository import IndexRepository
from app.schemas.retrieval import IndexStatus, SearchRequest, SearchResponse
from app.services.index_service import IndexService

router = APIRouter(prefix="/search", tags=["retrieval"])


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    service: Annotated[IndexService, Depends(get_index_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchResponse:
    try:
        results = service.search(
            request.query.strip(),
            request.k or settings.retrieval_k,
            settings.retrieval_score_threshold,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector index is incompatible and must be rebuilt.",
        ) from exc
    return SearchResponse(query=request.query, results=results, total=len(results))


@router.get("/index", response_model=IndexStatus | None)
async def index_status(
    repository: Annotated[IndexRepository, Depends(get_index_repository)],
) -> IndexStatus | None:
    return repository.get_status()


@router.post("/index/rebuild", response_model=IndexStatus)
async def rebuild_index(
    service: Annotated[IndexService, Depends(get_index_service)],
) -> IndexStatus:
    return service.rebuild()
