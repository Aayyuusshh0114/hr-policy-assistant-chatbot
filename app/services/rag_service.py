import json

from app.core.config import Settings
from app.core.exceptions import ConversationNotFoundError, ProviderError
from app.llms.base import LLMMessage, LLMProvider
from app.prompts.answer_prompt import build_answer_prompt
from app.prompts.contextualization_prompt import build_contextualization_prompt
from app.prompts.guardrails import SYSTEM_GUARDRAILS
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ChatResponse
from app.services.index_service import IndexService

REFUSAL = "I could not find this information in the available HR policies."


class RagService:
    def __init__(
        self,
        settings: Settings,
        conversations: ConversationRepository,
        index: IndexService,
        provider: LLMProvider,
    ) -> None:
        self.settings = settings
        self.conversations = conversations
        self.index = index
        self.provider = provider

    def ask(self, conversation_id: str, question: str) -> ChatResponse:
        if not self.conversations.exists(conversation_id):
            raise ConversationNotFoundError("Conversation not found.")

        history = self.conversations.messages(conversation_id, self.settings.max_history_messages)
        standalone = self._standalone_question(question.strip(), history)
        self.conversations.add_message(
            conversation_id,
            "user",
            question.strip(),
            standalone_question=standalone,
        )
        matches = self.index.search(
            standalone,
            self.settings.retrieval_k,
            self.settings.retrieval_score_threshold,
        )
        if not matches:
            message = self.conversations.add_message(
                conversation_id, "assistant", REFUSAL, provider=self.provider.name
            )
            return ChatResponse(
                conversation_id=conversation_id,
                message=message,
                insufficient_evidence=True,
            )

        context = "\n\n".join(
            f"CHUNK_ID: {match.chunk_id}\n"
            f"SOURCE: {match.filename}, page {match.page_number}\n"
            f"TEXT: {match.text}"
            for match in matches
        )
        raw_response = self.provider.complete(
            [
                LLMMessage(role="system", content=SYSTEM_GUARDRAILS),
                LLMMessage(role="user", content=build_answer_prompt(standalone, context)),
            ]
        )
        answer, used_chunk_ids = self._parse_grounded_response(raw_response)
        match_by_id = {match.chunk_id: match for match in matches}
        if any(chunk_id not in match_by_id for chunk_id in used_chunk_ids):
            raise ProviderError("The provider cited evidence that was not retrieved.")
        citations = [
            match_by_id[chunk_id]
            for chunk_id in used_chunk_ids
            if chunk_id in match_by_id
        ]

        insufficient = answer == REFUSAL or not citations
        if insufficient:
            answer = REFUSAL
            citations = []
        message = self.conversations.add_message(
            conversation_id,
            "assistant",
            answer,
            provider=self.provider.name,
            citations=citations,
        )
        return ChatResponse(
            conversation_id=conversation_id,
            message=message,
            insufficient_evidence=insufficient,
        )

    def _standalone_question(self, question: str, history: list) -> str:
        if not history:
            return question
        history_text = "\n".join(f"{message.role}: {message.content}" for message in history)
        rewritten = self.provider.complete(
            [
                LLMMessage(
                    role="system",
                    content="Rewrite conversational HR questions for document retrieval.",
                ),
                LLMMessage(
                    role="user",
                    content=build_contextualization_prompt(history_text, question),
                ),
            ]
        ).strip()
        return rewritten[:2000] or question

    @staticmethod
    def _parse_grounded_response(raw_response: str) -> tuple[str, list[str]]:
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```")
            cleaned = cleaned.removesuffix("```").strip()
        try:
            payload = json.loads(cleaned)
            answer = payload["answer"]
            chunk_ids = payload["used_chunk_ids"]
            if not isinstance(answer, str) or not isinstance(chunk_ids, list):
                raise ValueError
            if not all(isinstance(chunk_id, str) for chunk_id in chunk_ids):
                raise ValueError
            return answer.strip(), list(dict.fromkeys(chunk_ids))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ProviderError("The provider returned an invalid grounded response.") from exc
