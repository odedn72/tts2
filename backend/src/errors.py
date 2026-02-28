"""
Error hierarchy for the TTS Reader application.

All custom errors inherit from AppError. The FastAPI exception handler
catches AppError and returns structured JSON responses.
"""

import re


class AppError(Exception):
    """
    Base error for all application errors.

    All custom errors inherit from this. The FastAPI exception handler
    catches AppError and returns structured JSON responses.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        http_status: int = 500,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}


# --- Validation Errors ---


class ValidationError(AppError):
    """Invalid input data."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            http_status=400,
            details=details,
        )


class TextEmptyError(ValidationError):
    """Text input is empty or whitespace-only."""

    def __init__(self) -> None:
        super().__init__(
            message="Text input cannot be empty",
            details={"field": "text"},
        )


# --- Provider Errors ---


class ProviderError(AppError):
    """Base class for all provider-related errors."""

    pass


class ProviderNotFoundError(ProviderError):
    """Requested provider does not exist."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' is not available",
            error_code="INVALID_PROVIDER",
            http_status=400,
            details={"provider": provider},
        )


class ProviderNotConfiguredError(ProviderError):
    """Provider exists but has no API key configured."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Provider '{provider}' is not configured. Please set the API key in Settings.",
            error_code="PROVIDER_NOT_CONFIGURED",
            http_status=400,
            details={"provider": provider},
        )


class ProviderAuthError(ProviderError):
    """Provider rejected our credentials."""

    def __init__(self, provider: str, detail: str = "") -> None:
        msg = f"Authentication failed for provider '{provider}'"
        if detail:
            msg += f": {detail}"
        super().__init__(
            message=msg,
            error_code="PROVIDER_AUTH_ERROR",
            http_status=502,
            details={"provider": provider},
        )


class ProviderAPIError(ProviderError):
    """Provider API returned an error."""

    def __init__(self, provider: str, detail: str = "") -> None:
        msg = f"Provider '{provider}' returned an error"
        if detail:
            msg += f": {detail}"
        super().__init__(
            message=msg,
            error_code="PROVIDER_API_ERROR",
            http_status=502,
            details={"provider": provider},
        )


class ProviderRateLimitError(ProviderError):
    """Provider rate limit exceeded."""

    def __init__(self, provider: str) -> None:
        super().__init__(
            message=f"Rate limit exceeded for provider '{provider}'. Please wait and try again.",
            error_code="PROVIDER_RATE_LIMIT",
            http_status=429,
            details={"provider": provider},
        )


# --- Job Errors ---


class JobNotFoundError(AppError):
    """No job with the given ID exists."""

    def __init__(self, job_id: str) -> None:
        super().__init__(
            message=f"Job '{job_id}' not found",
            error_code="JOB_NOT_FOUND",
            http_status=404,
            details={"job_id": job_id},
        )


class JobNotCompletedError(AppError):
    """Job exists but audio is not yet available."""

    def __init__(self, job_id: str, status: str) -> None:
        super().__init__(
            message=f"Job '{job_id}' is not completed (current status: {status})",
            error_code="JOB_NOT_COMPLETED",
            http_status=409,
            details={"job_id": job_id, "status": status},
        )


# --- Audio Processing Errors ---


class AudioProcessingError(AppError):
    """Error during audio stitching or file operations."""

    def __init__(self, detail: str = "") -> None:
        msg = "Audio processing failed"
        if detail:
            msg += f": {detail}"
        super().__init__(
            message=msg,
            error_code="AUDIO_PROCESSING_ERROR",
            http_status=500,
        )


# --- Sanitization ---


def sanitize_provider_error(raw_message: str) -> str:
    """
    Remove any potentially sensitive information from provider error messages.

    Strips anything that looks like an API key (20+ alphanumeric characters)
    and URLs with query parameters.
    """
    sanitized = re.sub(r"[A-Za-z0-9_\-]{20,}", "[REDACTED]", raw_message)
    sanitized = re.sub(r"https?://\S+", "[URL REDACTED]", sanitized)
    return sanitized
