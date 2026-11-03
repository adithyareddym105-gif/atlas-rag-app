import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class GeneratedAnswer(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    not_found: bool = False


def generate_answer(query: str, chunks: list[dict]) -> GeneratedAnswer:
    if not chunks:
        return GeneratedAnswer(
            answer="I could not find relevant information in the selected documents.",
            citations=[],
            not_found=True,
        )

    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    if not api_key or not model:
        raise RuntimeError("LLM_API_KEY or LLM_MODEL is missing from .env")

    client = OpenAI(api_key=api_key, base_url=base_url)

    evidence = "\n\n".join(
        f"Chunk ID: {chunk['chunk_id']}\nSource: {chunk['source']}\nContent:\n{chunk['text']}"
        for chunk in chunks
    )

    response = client.chat.completions.create(
        model=model,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document question-answering assistant. "
                    "Use ONLY the supplied evidence. Never use outside knowledge. "
                    "If the evidence does not contain the answer, say so clearly. "
                    "Cite the chunk IDs that support your answer. "
                    "Return valid JSON with exactly these fields: "
                    '{"answer": "string", "citations": ["chunk_id"], "not_found": false}. '
                    "Set not_found to true when the evidence is insufficient."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nEvidence:\n{evidence}",
            },
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The LLM returned an empty response")

    result = GeneratedAnswer.model_validate_json(content)

    allowed_ids = {chunk["chunk_id"] for chunk in chunks}
    invalid_ids = set(result.citations) - allowed_ids
    if invalid_ids:
        raise ValueError("The LLM cited chunks that were not retrieved")

    return result
