from app.core.config import Settings
from app.core.exceptions import ProviderConfigurationError
from app.llms.base import LLMProvider
from app.llms.gemini_provider import GeminiProvider
from app.llms.groq_provider import GroqProvider


def create_provider(name: str, settings: Settings) -> LLMProvider:
    if name == "groq":
        if not settings.groq_api_key:
            raise ProviderConfigurationError("Groq is selected but GROQ_API_KEY is not configured.")
        return GroqProvider(settings.groq_api_key, settings.groq_model)
    if name == "gemini":
        if not settings.gemini_api_key:
            raise ProviderConfigurationError(
                "Gemini is selected but GEMINI_API_KEY is not configured."
            )
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    raise ProviderConfigurationError(f"Unsupported LLM provider: {name}")

