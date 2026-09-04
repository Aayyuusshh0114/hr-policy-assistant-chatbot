from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_conversation_repository, get_index_service
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    ConversationNotFoundError,
    ProviderConfigurationError,
    ProviderError,
)
from app.llms.factory import create_provider
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ChatRequest, ChatResponse, ProviderInfo
from app.services.index_service import IndexService
from app.services.rag_service import RagService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    conversations: Annotated[
        ConversationRepository, Depends(get_conversation_repository)
    ],
    index: Annotated[IndexService, Depends(get_index_service)],
) -> ChatResponse:
    provider_name = request.provider or settings.llm_provider
    try:
        provider = create_provider(provider_name, settings)
        return RagService(settings, conversations, index, provider).ask(
            request.conversation_id, request.question
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/providers", response_model=list[ProviderInfo])
async def providers(
    settings: Annotated[Settings, Depends(get_settings)],
) -> list[ProviderInfo]:
    return [
        ProviderInfo(
            name="groq",
            configured=bool(settings.groq_api_key),
            model=settings.groq_model,
        ),
        ProviderInfo(
            name="gemini",
            configured=bool(settings.gemini_api_key),
            model=settings.gemini_model,
        ),
    ]
