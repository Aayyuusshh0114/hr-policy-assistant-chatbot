from groq import Groq

from app.core.exceptions import ProviderError
from app.llms.base import LLMMessage


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model_name: str) -> None:
        self._model_name = model_name
        self.client = Groq(api_key=api_key, timeout=30.0, max_retries=1)

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete(self, messages: list[LLMMessage]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": message.role, "content": message.content}
                    for message in messages
                ],
                temperature=0,
            )
            content = response.choices[0].message.content
            if not content:
                raise ProviderError("Groq returned an empty response.")
            return content.strip()
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Groq could not generate a response.") from exc
