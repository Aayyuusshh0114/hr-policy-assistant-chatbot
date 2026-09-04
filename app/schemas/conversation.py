from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    excerpt: str


class MessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    provider: str | None
    standalone_question: str | None
    citations: list[CitationResponse] = Field(default_factory=list)
    created_at: datetime


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=100)


class ChatRequest(BaseModel):
    conversation_id: str
    question: str = Field(min_length=2, max_length=2000)
    provider: Literal["groq", "gemini"] | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    insufficient_evidence: bool


class ProviderInfo(BaseModel):
    name: Literal["groq", "gemini"]
    configured: bool
    model: str
