# TDD: Written from spec 11-error-handling.md
# Tests for the error hierarchy defined in backend/src/errors.py

import pytest


class TestAppError:
    """Tests for the base AppError class."""

    def test_app_error_default_values(self):
        from src.errors import AppError

        err = AppError("Something went wrong")
        assert err.message == "Something went wrong"
        assert err.error_code == "INTERNAL_ERROR"
        assert err.http_status == 500
        assert err.details == {}

    def test_app_error_custom_values(self):
        from src.errors import AppError

        err = AppError(
            message="Custom error",
            error_code="CUSTOM",
            http_status=418,
            details={"key": "value"},
        )
        assert err.message == "Custom error"
        assert err.error_code == "CUSTOM"
        assert err.http_status == 418
        assert err.details == {"key": "value"}

    def test_app_error_is_exception(self):
        from src.errors import AppError

        err = AppError("test")
        assert isinstance(err, Exception)

    def test_app_error_str_representation(self):
        from src.errors import AppError

        err = AppError("Something went wrong")
        assert str(err) == "Something went wrong"


class TestValidationError:
    """Tests for ValidationError and its subclasses."""

    def test_validation_error_defaults(self):
        from src.errors import ValidationError

        err = ValidationError("Invalid input")
        assert err.error_code == "VALIDATION_ERROR"
        assert err.http_status == 400
        assert err.message == "Invalid input"

    def test_validation_error_with_details(self):
        from src.errors import ValidationError

        err = ValidationError("Bad field", details={"field": "name"})
        assert err.details == {"field": "name"}

    def test_validation_error_inherits_app_error(self):
        from src.errors import ValidationError, AppError

        err = ValidationError("test")
        assert isinstance(err, AppError)

    def test_text_empty_error(self):
        from src.errors import TextEmptyError

        err = TextEmptyError()
        assert err.error_code == "VALIDATION_ERROR"
        assert err.http_status == 400
        assert "empty" in err.message.lower()
        assert err.details == {"field": "text"}

    def test_text_empty_error_inherits_validation_error(self):
        from src.errors import TextEmptyError, ValidationError

        err = TextEmptyError()
        assert isinstance(err, ValidationError)


class TestProviderErrors:
    """Tests for all provider-related error classes."""

    def test_provider_not_found_error(self):
        from src.errors import ProviderNotFoundError

        err = ProviderNotFoundError("google")
        assert err.error_code == "INVALID_PROVIDER"
        assert err.http_status == 400
        assert "google" in err.message
        assert err.details == {"provider": "google"}

    def test_provider_not_configured_error(self):
        from src.errors import ProviderNotConfiguredError

        err = ProviderNotConfiguredError("openai")
        assert err.error_code == "PROVIDER_NOT_CONFIGURED"
        assert err.http_status == 400
        assert "openai" in err.message
        assert "Settings" in err.message or "configured" in err.message.lower()

    def test_provider_auth_error_without_detail(self):
        from src.errors import ProviderAuthError

        err = ProviderAuthError("elevenlabs")
        assert err.error_code == "PROVIDER_AUTH_ERROR"
        assert err.http_status == 502
        assert "elevenlabs" in err.message
        assert "Authentication" in err.message or "authentication" in err.message

    def test_provider_auth_error_with_detail(self):
        from src.errors import ProviderAuthError

        err = ProviderAuthError("google", detail="Invalid credentials")
        assert "Invalid credentials" in err.message

    def test_provider_api_error_without_detail(self):
        from src.errors import ProviderAPIError

        err = ProviderAPIError("amazon")
        assert err.error_code == "PROVIDER_API_ERROR"
        assert err.http_status == 502
        assert "amazon" in err.message

    def test_provider_api_error_with_detail(self):
        from src.errors import ProviderAPIError

        err = ProviderAPIError("google", detail="quota exceeded")
        assert "quota exceeded" in err.message

    def test_provider_rate_limit_error(self):
        from src.errors import ProviderRateLimitError

        err = ProviderRateLimitError("elevenlabs")
        assert err.error_code == "PROVIDER_RATE_LIMIT"
        assert err.http_status == 429
        assert "elevenlabs" in err.message
        assert "rate limit" in err.message.lower() or "Rate limit" in err.message

    def test_provider_errors_inherit_from_provider_error(self):
        from src.errors import (
            ProviderError,
            ProviderNotFoundError,
            ProviderNotConfiguredError,
            ProviderAuthError,
            ProviderAPIError,
            ProviderRateLimitError,
        )

        assert isinstance(ProviderNotFoundError("x"), ProviderError)
        assert isinstance(ProviderNotConfiguredError("x"), ProviderError)
        assert isinstance(ProviderAuthError("x"), ProviderError)
        assert isinstance(ProviderAPIError("x"), ProviderError)
        assert isinstance(ProviderRateLimitError("x"), ProviderError)

    def test_provider_error_inherits_app_error(self):
        from src.errors import ProviderError, AppError

        err = ProviderError(
            message="test",
            error_code="TEST",
            http_status=500,
        )
        assert isinstance(err, AppError)


class TestJobErrors:
    """Tests for job-related error classes."""

    def test_job_not_found_error(self):
        from src.errors import JobNotFoundError

        err = JobNotFoundError("abc-123")
        assert err.error_code == "JOB_NOT_FOUND"
        assert err.http_status == 404
        assert "abc-123" in err.message
        assert err.details == {"job_id": "abc-123"}

    def test_job_not_completed_error(self):
        from src.errors import JobNotCompletedError

        err = JobNotCompletedError("abc-123", "in_progress")
        assert err.error_code == "JOB_NOT_COMPLETED"
        assert err.http_status == 409
        assert "abc-123" in err.message
        assert "in_progress" in err.message
        assert err.details["job_id"] == "abc-123"
        assert err.details["status"] == "in_progress"


class TestAudioProcessingError:
    """Tests for AudioProcessingError."""

    def test_audio_processing_error_without_detail(self):
        from src.errors import AudioProcessingError

        err = AudioProcessingError()
        assert err.error_code == "AUDIO_PROCESSING_ERROR"
        assert err.http_status == 500
        assert "Audio processing failed" in err.message

    def test_audio_processing_error_with_detail(self):
        from src.errors import AudioProcessingError

        err = AudioProcessingError(detail="invalid mp3 data")
        assert "invalid mp3 data" in err.message


class TestErrorHierarchy:
    """Tests to verify the complete error inheritance tree."""

    def test_all_errors_caught_by_app_error(self):
        from src.errors import (
            AppError,
            ValidationError,
            TextEmptyError,
            ProviderNotFoundError,
            ProviderNotConfiguredError,
            ProviderAuthError,
            ProviderAPIError,
            ProviderRateLimitError,
            JobNotFoundError,
            JobNotCompletedError,
            AudioProcessingError,
        )

        errors = [
            ValidationError("x"),
            TextEmptyError(),
            ProviderNotFoundError("x"),
            ProviderNotConfiguredError("x"),
            ProviderAuthError("x"),
            ProviderAPIError("x"),
            ProviderRateLimitError("x"),
            JobNotFoundError("x"),
            JobNotCompletedError("x", "pending"),
            AudioProcessingError(),
        ]
        for err in errors:
            assert isinstance(err, AppError), f"{type(err).__name__} is not an AppError"
