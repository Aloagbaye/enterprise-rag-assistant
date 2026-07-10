from typing import Any


def validate_answer_grounding(
    answer_payload: dict[str, Any],
    retrieved_docs: list[dict]
) -> dict[str, Any]:
    """
    Basic grounding guardrail.

    Checks:
    1. The model returned an answer.
    2. The model's cited sources exist in the retrieved documents.
    3. If no documents were retrieved, the answer should not pretend to know.
    """

    retrieved_sources = {
        doc.get("source_file")
        for doc in retrieved_docs
        if doc.get("source_file")
    }

    cited_sources = set(answer_payload.get("sources", []))
    answer = answer_payload.get("answer", "")

    if not retrieved_docs:
        return {
            "status": "no_context",
            "passed": False,
            "reason": "No documents were retrieved."
        }

    if not answer:
        return {
            "status": "failed",
            "passed": False,
            "reason": "Answer is empty."
        }

    invalid_sources = cited_sources - retrieved_sources

    if invalid_sources:
        return {
            "status": "failed",
            "passed": False,
            "reason": f"Answer cited sources that were not retrieved: {sorted(invalid_sources)}"
        }

    if not cited_sources:
        return {
            "status": "warning",
            "passed": True,
            "reason": "Answer did not cite sources, but context was retrieved."
        }

    return {
        "status": "passed",
        "passed": True,
        "reason": "Answer sources match retrieved documents."
    }


def apply_guardrail_fallback(
    answer_payload: dict[str, Any],
    guardrail_result: dict[str, Any]
) -> dict[str, Any]:
    """
    If grounding fails, return a safer answer.
    """

    if guardrail_result["passed"]:
        return answer_payload

    return {
        "answer": (
            "I do not have enough reliable information from the authorized "
            "retrieved documents to answer this question."
        ),
        "sources": [],
        "confidence": "low",
        "grounding_notes": guardrail_result["reason"]
    }