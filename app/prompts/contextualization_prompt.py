def build_contextualization_prompt(history: str, question: str) -> str:
    return f"""Rewrite the current HR question as a standalone search query.
Use history only to resolve references such as it, they, or this policy.
Do not answer, add facts, or change the subject. Return only the rewritten question.

Conversation history:
{history}

Current question:
{question}"""

