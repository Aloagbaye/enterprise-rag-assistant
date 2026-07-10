import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record, default=str)


def configure_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    # Avoid duplicate handlers during reloads.
    if logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)


def configure_application_insights() -> None:
    """
    Optional Application Insights setup.

    For local tutorial work, this can stay disabled.
    When MONITORING_ENABLED=true and a connection string is provided,
    telemetry can be sent to Azure Monitor Application Insights.
    """

    if not settings.monitoring_enabled:
        return

    if not settings.appinsights_connection_string:
        logging.warning(
            "MONITORING_ENABLED=true but APPLICATIONINSIGHTS_CONNECTION_STRING is empty"
        )
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.appinsights_connection_string
        )

        logging.info("Azure Monitor Application Insights configured")

    except Exception:
        logging.exception("Failed to configure Azure Monitor Application Insights")


def instrument_fastapi(app: Any) -> None:
    if not settings.monitoring_enabled:
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logging.info("FastAPI OpenTelemetry instrumentation enabled")

    except Exception:
        logging.exception("Failed to instrument FastAPI app")


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event_name: str,
    level: int = logging.INFO,
    **kwargs: Any
) -> None:
    logger.log(
        level,
        event_name,
        extra={
            "extra_data": {
                "event_name": event_name,
                **kwargs
            }
        }
    )


def safe_doc_metadata(doc: dict) -> dict:
    """
    Avoid logging full document content by default.
    """

    return {
        "id": doc.get("id"),
        "source_file": doc.get("source_file"),
        "department": doc.get("department"),
        "security_level": doc.get("security_level"),
        "allowed_roles": doc.get("allowed_roles"),
    }


def summarize_token_usage(usage: Optional[Any]) -> dict:
    if not usage:
        return {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }

    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }