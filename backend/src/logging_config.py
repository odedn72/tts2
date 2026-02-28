"""
Structured logging configuration for the TTS Reader backend.

In production (LOG_FORMAT=json), emits JSON-structured log lines.
In development (LOG_FORMAT=text, the default), uses human-readable format.
"""

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone


class KeyRedactingFilter(logging.Filter):
    """Redact potential API keys from log messages."""

    KEY_PATTERN = re.compile(r"[A-Za-z0-9_\-]{20,}")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.KEY_PATTERN.sub("[REDACTED]", record.msg)
        return True


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Includes timestamp, level, logger name, message, and any extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request_id if present (set by RequestIDMiddleware)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Include exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_entry, default=str)


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Reads LOG_FORMAT and LOG_LEVEL from environment variables:
      - LOG_FORMAT: "json" for structured output, "text" for development (default: "text")
      - LOG_LEVEL: standard Python log level name (default: "INFO")
    """
    log_format = os.environ.get("LOG_FORMAT", "text").lower()
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    handler.addFilter(KeyRedactingFilter())
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
