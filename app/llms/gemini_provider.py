from google import genai
from google.genai import types

from app.core.exceptions import ProviderError
from app.llms.base import LLMMessage


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model_name: str) -> None:
        self._model_name = model_name
        self.client = genai.Client(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete(self, messages: list[LLMMessage]) -> str:
        system_parts = [message.content for message in messages if message.role == "system"]
        conversation = "\n\n".join(
            f"{message.role.upper()}: {message.content}"
            for message in messages
            if message.role != "system"
        )
        try:
            response = self.client.models.generate_content(
                model=self._model_name,
                contents=conversation,
                config=types.GenerateContentConfig(
                    system_instruction="\n\n".join(system_parts),
                    temperature=0,
                ),
            )
            if not response.text:
                raise ProviderError("Gemini returned an empty response.")
            return response.text.strip()
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Gemini could not generate a response.") from exc

