from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    application: str
    version: str
    environment: str


class ProviderStatus(BaseModel):
    configured: bool


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    runtime_directories: dict[str, bool]
    selected_provider: Literal["groq", "gemini"]
    providers: dict[str, ProviderStatus]
    capabilities: dict[str, bool]

