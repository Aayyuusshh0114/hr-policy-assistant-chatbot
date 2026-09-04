from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.schemas.health import HealthResponse, ProviderStatus, ReadinessResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=__version__,
        environment=settings.app_env,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    settings = get_settings()
    directory_status = settings.runtime_directory_status()
    return ReadinessResponse(
        status="ready" if all(directory_status.values()) else "not_ready",
        runtime_directories=directory_status,
        selected_provider=settings.llm_provider,
        providers={
            "groq": ProviderStatus(configured=bool(settings.groq_api_key)),
            "gemini": ProviderStatus(configured=bool(settings.gemini_api_key)),
        },
        capabilities={
            "document_ingestion": True,
            "vector_search": True,
            "chat": True,
        },
    )
