import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderConfigurationError
from app.llms.factory import create_provider


@pytest.mark.parametrize("provider", ["groq", "gemini"])
def test_provider_requires_api_key(provider: str) -> None:
    settings = Settings(_env_file=None, groq_api_key=None, gemini_api_key=None)

    with pytest.raises(ProviderConfigurationError):
        create_provider(provider, settings)


def test_unsupported_provider_is_rejected() -> None:
    with pytest.raises(ProviderConfigurationError, match="Unsupported"):
        create_provider("unknown", Settings(_env_file=None))

