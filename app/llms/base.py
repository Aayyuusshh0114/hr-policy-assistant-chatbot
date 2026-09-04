from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def model_name(self) -> str: ...

    def complete(self, messages: list[LLMMessage]) -> str: ...

