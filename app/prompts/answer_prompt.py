def build_answer_prompt(question: str, context: str) -> str:
    return f"""Answer the question using only the policy excerpts below.
Each excerpt begins with a chunk ID. Cite only IDs that directly support the answer.

Answer-quality requirements:
- Give the conclusion first, followed by conditions or exceptions that materially affect it.
- Use plain professional language suitable for workplace communication.
- Do not mention chunk IDs, retrieval, excerpts, or the model in the answer text.
- Do not infer an entitlement, approval, deadline, or exception that is not explicit.
- If policies conflict, state the conflict instead of choosing one silently.

Return JSON exactly in this shape:
{{"answer": "answer text", "used_chunk_ids": ["chunk-id"]}}

If context is insufficient, return:
{{
  "answer": "I could not find this information in the available HR policies.",
  "used_chunk_ids": []
}}

POLICY EXCERPTS:
{context}

QUESTION:
{question}"""
