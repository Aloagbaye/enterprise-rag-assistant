from app.guardrails import validate_answer_grounding, apply_guardrail_fallback


def test_grounded_answer_passes():
    docs = [
        {
            "id": "finance_001",
            "source_file": "finance_q4_forecast.txt"
        }
    ]

    answer = {
        "answer": "Demand increased by 7%.",
        "sources": ["finance_q4_forecast.txt"],
        "confidence": "high"
    }

    result = validate_answer_grounding(answer, docs)

    assert result["passed"] is True
    assert result["status"] == "passed"


def test_answer_with_invalid_source_fails():
    docs = [
        {
            "id": "finance_001",
            "source_file": "finance_q4_forecast.txt"
        }
    ]

    answer = {
        "answer": "Demand increased by 7%.",
        "sources": ["unknown_file.txt"],
        "confidence": "high"
    }

    result = validate_answer_grounding(answer, docs)

    assert result["passed"] is False
    assert result["status"] == "failed"


def test_fallback_replaces_failed_answer():
    answer = {
        "answer": "Unsupported claim.",
        "sources": ["unknown_file.txt"],
        "confidence": "high"
    }

    guardrail_result = {
        "passed": False,
        "status": "failed",
        "reason": "Invalid source"
    }

    fallback = apply_guardrail_fallback(answer, guardrail_result)

    assert fallback["confidence"] == "low"
    assert fallback["sources"] == []