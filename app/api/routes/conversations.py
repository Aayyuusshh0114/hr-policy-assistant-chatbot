from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_conversation_repository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ConversationDetail,
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationResponse:
    return repository.create(request.title)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationListResponse:
    conversations = repository.list()
    return ConversationListResponse(conversations=conversations, total=len(conversations))


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> ConversationDetail:
    conversation = repository.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    repository: Annotated[ConversationRepository, Depends(get_conversation_repository)],
) -> None:
    if not repository.delete(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")

