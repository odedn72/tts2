"""
Tests for the structured logging configuration.

Verifies that:
  - JSON formatter produces valid JSON output
  - Text formatter produces human-readable output
  - configure_logging respects LOG_FORMAT and LOG_LEVEL env vars
"""

import json
import logging
import os

import pytest

from src.logging_config import JSONFormatter, configure_logging


class TestJSONFormatter:
    """Tests for the JSONFormatter."""

    def test_format_produces_valid_json(self):
        """Output should be valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("world",),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "Hello world"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"

    def test_format_includes_timestamp(self):
        """JSON output should include an ISO timestamp."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "timestamp" in data
        # ISO format should contain 'T'
        assert "T" in data["timestamp"]

    def test_format_includes_request_id_when_present(self):
        """If record has request_id attribute, it should appear in JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc-123"
        output = formatter.format(record)
        data = json.loads(output)
        assert data["request_id"] == "abc-123"

    def test_format_excludes_request_id_when_absent(self):
        """If record does not have request_id, it should not appear in JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "request_id" not in data

    def test_format_includes_exception_info(self):
        """Exception info should be captured in the JSON output."""
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="something failed",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "test error" in data["exception"]["message"]


class TestConfigureLogging:
    """Tests for the configure_logging function."""

    def test_configure_logging_text_format(self, monkeypatch):
        """Text format should use a human-readable formatter."""
        monkeypatch.setenv("LOG_FORMAT", "text")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        configure_logging()

        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) > 0
        # Text formatter should NOT be JSONFormatter
        assert not isinstance(root.handlers[0].formatter, JSONFormatter)

    def test_configure_logging_json_format(self, monkeypatch):
        """JSON format should use JSONFormatter."""
        monkeypatch.setenv("LOG_FORMAT", "json")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        configure_logging()

        root = logging.getLogger()
        assert root.level == logging.WARNING
        assert len(root.handlers) > 0
        assert isinstance(root.handlers[0].formatter, JSONFormatter)

    def test_configure_logging_defaults(self, monkeypatch):
        """Without env vars, should default to text format and INFO level."""
        monkeypatch.delenv("LOG_FORMAT", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        configure_logging()

        root = logging.getLogger()
        assert root.level == logging.INFO
        assert not isinstance(root.handlers[0].formatter, JSONFormatter)
