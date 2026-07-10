import json
from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.config import settings
from app.secrets import get_azure_openai_api_key, get_azure_openai_chat_api_key


@lru_cache
def get_openai_client() -> OpenAI:
    if not settings.azure_openai_endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT is not configured.")

    return OpenAI(
        api_key=get_azure_openai_api_key(),
        base_url=f"{settings.azure_openai_endpoint.rstrip('/')}/openai/v1/"
    )


@lru_cache
def get_chat_openai_client() -> OpenAI:
    endpoint = settings.azure_openai_chat_endpoint or settings.azure_openai_endpoint

    if not endpoint:
        raise ValueError(
            "AZURE_OPENAI_CHAT_ENDPOINT or AZURE_OPENAI_ENDPOINT is not configured."
        )

    if not settings.azure_openai_chat_deployment:
        raise ValueError("AZURE_OPENAI_CHAT_DEPLOYMENT is not configured.")

    return OpenAI(
        api_key=get_azure_openai_chat_api_key(),
        base_url=f"{endpoint.rstrip('/')}/openai/v1/"
    )


def embed_text(text: str) -> list[float]:
    client = get_openai_client()

    response = client.embeddings.create(
        model=settings.azure_openai_embedding_deployment,
        input=text
    )

    return response.data[0].embedding


def generate_grounded_response(
    question: str,
    context: str
) -> tuple[dict[str, Any], Any]:
    """
    Generate a grounded answer from retrieved context.

    Returns:
        parsed_response, usage
    """

    client = get_chat_openai_client()

    system_prompt = """
You are a secure enterprise RAG assistant.

Rules:
- Answer only using the provided context.
- Do not use outside knowledge.
- If the context does not contain enough information, say so.
- Include only source files that appear in the provided context.
- Return valid JSON only.

JSON format:
{
  "answer": "your grounded answer",
  "sources": ["source_file_name"],
  "confidence": "high | medium | low",
  "grounding_notes": "brief explanation of why the answer is grounded"
}
""".strip()

    user_prompt = f"""
Question:
{question}

Retrieved Context:
{context}
""".strip()

    response = client.chat.completions.create(
        model=settings.azure_openai_chat_deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            "answer": content,
            "sources": [],
            "confidence": "low",
            "grounding_notes": "Model did not return valid JSON."
        }

    return parsed, response.usage