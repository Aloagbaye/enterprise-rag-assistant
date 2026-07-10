import time
import uuid
from typing import Any

from app.auth import UserContext
from app.config import settings
from app.guardrails import apply_guardrail_fallback, validate_answer_grounding
from app.monitoring import (
    get_logger,
    log_event,
    safe_doc_metadata,
    summarize_token_usage,
)
from app.openai_client import generate_grounded_response
from app.search_client import search_documents


logger = get_logger(__name__)


def build_context_from_docs(docs: list[dict]) -> str:
    context_blocks = []

    for idx, doc in enumerate(docs, start=1):
        context_blocks.append(
            f"""
[Document {idx}]
id: {doc.get("id")}
source_file: {doc.get("source_file")}
department: {doc.get("department")}
security_level: {doc.get("security_level")}
content: {doc.get("content")}
""".strip()
        )

    return "\n\n".join(context_blocks)


def run_rag_pipeline(
    question: str,
    user: UserContext,
    top_k: int = 3
) -> dict[str, Any]:
    request_id = str(uuid.uuid4())
    total_start = time.perf_counter()

    log_event(
        logger,
        "rag_request_started",
        request_id=request_id,
        user_id=user.user_id,
        roles=user.roles,
        question_length=len(question),
    )

    try:
        retrieval_start = time.perf_counter()

        retrieved_docs = search_documents(
            question=question,
            user_roles=user.roles,
            top_k=top_k
        )

        retrieval_latency_ms = round((time.perf_counter() - retrieval_start) * 1000)

        doc_metadata = [safe_doc_metadata(doc) for doc in retrieved_docs]

        log_event(
            logger,
            "rag_retrieval_completed",
            request_id=request_id,
            user_id=user.user_id,
            roles=user.roles,
            retrieved_doc_ids=[doc["id"] for doc in retrieved_docs],
            source_files=[doc["source_file"] for doc in retrieved_docs],
            retrieval_latency_ms=retrieval_latency_ms,
        )

        if not retrieved_docs:
            total_latency_ms = round((time.perf_counter() - total_start) * 1000)

            log_event(
                logger,
                "rag_no_documents_retrieved",
                request_id=request_id,
                user_id=user.user_id,
                roles=user.roles,
                total_latency_ms=total_latency_ms,
            )

            return {
                "request_id": request_id,
                "answer": (
                    "I could not find any authorized documents that answer this question."
                ),
                "sources": [],
                "confidence": "low",
                "guardrail_status": "no_context",
                "retrieved_documents": [],
                "latency_ms": {
                    "retrieval": retrieval_latency_ms,
                    "generation": 0,
                    "total": total_latency_ms,
                },
                "token_usage": {
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None,
                }
            }

        context = build_context_from_docs(retrieved_docs)

        generation_start = time.perf_counter()

        answer_payload, usage = generate_grounded_response(
            question=question,
            context=context
        )

        generation_latency_ms = round((time.perf_counter() - generation_start) * 1000)

        guardrail_result = validate_answer_grounding(
            answer_payload=answer_payload,
            retrieved_docs=retrieved_docs
        )

        final_answer_payload = apply_guardrail_fallback(
            answer_payload=answer_payload,
            guardrail_result=guardrail_result
        )

        total_latency_ms = round((time.perf_counter() - total_start) * 1000)
        token_usage = summarize_token_usage(usage)

        log_payload = {
            "request_id": request_id,
            "user_id": user.user_id,
            "roles": user.roles,
            "question_length": len(question),
            "retrieved_doc_ids": [doc["id"] for doc in retrieved_docs],
            "source_files": [doc["source_file"] for doc in retrieved_docs],
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": generation_latency_ms,
            "total_latency_ms": total_latency_ms,
            "guardrail_status": guardrail_result["status"],
            "guardrail_reason": guardrail_result["reason"],
            **token_usage,
        }

        if settings.log_full_prompts:
            log_payload["question"] = question
            log_payload["context"] = context

        log_event(
            logger,
            "rag_request_completed",
            **log_payload,
        )

        return {
            "request_id": request_id,
            "answer": final_answer_payload.get("answer"),
            "sources": final_answer_payload.get("sources", []),
            "confidence": final_answer_payload.get("confidence", "low"),
            "grounding_notes": final_answer_payload.get("grounding_notes"),
            "guardrail_status": guardrail_result["status"],
            "guardrail_reason": guardrail_result["reason"],
            "retrieved_documents": doc_metadata,
            "latency_ms": {
                "retrieval": retrieval_latency_ms,
                "generation": generation_latency_ms,
                "total": total_latency_ms,
            },
            "token_usage": token_usage
        }

    except Exception as exc:
        total_latency_ms = round((time.perf_counter() - total_start) * 1000)

        log_event(
            logger,
            "rag_request_failed",
            level=40,
            request_id=request_id,
            user_id=user.user_id,
            roles=user.roles,
            question_length=len(question),
            total_latency_ms=total_latency_ms,
            error=str(exc),
        )

        raise