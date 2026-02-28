# 11 - Error Handling

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the error hierarchy, error codes, and error handling patterns for both
backend and frontend.

**MRD traceability:** NFR-004 (no key exposure in errors), NFR-006 (graceful
error handling, clear messages, preserve partial results).

## Backend Error Hierarchy

```python
# errors.py

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
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        self.details = details or {}


# --- Validation Errors ---

class ValidationError(AppError):
    """Invalid input data."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            http_status=400,
            details=details,
        )


class TextEmptyError(ValidationError):
    """Text input is empty or whitespace-only."""
    def __init__(self):
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
    def __init__(self, provider: str):
        super().__init__(
            message=f"Provider '{provider}' is not available",
            error_code="INVALID_PROVIDER",
            http_status=400,
            details={"provider": provider},
        )


class ProviderNotConfiguredError(ProviderError):
    """Provider exists but has no API key configured."""
    def __init__(self, provider: str):
        super().__init__(
            message=f"Provider '{provider}' is not configured. Please set the API key in Settings.",
            error_code="PROVIDER_NOT_CONFIGURED",
            http_status=400,
            details={"provider": provider},
        )


class ProviderAuthError(ProviderError):
    """Provider rejected our credentials."""
    def __init__(self, provider: str, detail: str = ""):
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
    def __init__(self, provider: str, detail: str = ""):
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
    def __init__(self, provider: str):
        super().__init__(
            message=f"Rate limit exceeded for provider '{provider}'. Please wait and try again.",
            error_code="PROVIDER_RATE_LIMIT",
            http_status=429,
            details={"provider": provider},
        )


# --- Job Errors ---

class JobNotFoundError(AppError):
    """No job with the given ID exists."""
    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job '{job_id}' not found",
            error_code="JOB_NOT_FOUND",
            http_status=404,
            details={"job_id": job_id},
        )


class JobNotCompletedError(AppError):
    """Job exists but audio is not yet available."""
    def __init__(self, job_id: str, status: str):
        super().__init__(
            message=f"Job '{job_id}' is not completed (current status: {status})",
            error_code="JOB_NOT_COMPLETED",
            http_status=409,
            details={"job_id": job_id, "status": status},
        )


# --- Audio Processing Errors ---

class AudioProcessingError(AppError):
    """Error during audio stitching or file operations."""
    def __init__(self, detail: str = ""):
        msg = "Audio processing failed"
        if detail:
            msg += f": {detail}"
        super().__init__(
            message=msg,
            error_code="AUDIO_PROCESSING_ERROR",
            http_status=500,
        )
```

## Error Hierarchy Diagram

```
AppError
  +-- ValidationError
  |     +-- TextEmptyError
  +-- ProviderError
  |     +-- ProviderNotFoundError
  |     +-- ProviderNotConfiguredError
  |     +-- ProviderAuthError
  |     +-- ProviderAPIError
  |     +-- ProviderRateLimitError
  +-- JobNotFoundError
  +-- JobNotCompletedError
  +-- AudioProcessingError
```

## FastAPI Error Handler Registration

```python
# main.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full exception for debugging
    import logging
    logging.exception("Unhandled exception")

    # Return a generic error to the client (never expose internals)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )
```

## Frontend Error Handling

### API Client Error Mapping

```typescript
// api/client.ts

class ApiClientError extends Error {
  constructor(
    public code: string,
    public message: string,
    public details: Record<string, unknown> | null,
    public httpStatus: number,
  ) {
    super(message);
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiClientError(
      body?.error_code || "UNKNOWN_ERROR",
      body?.message || `HTTP ${response.status}: ${response.statusText}`,
      body?.details || null,
      response.status,
    );
  }
  return response.json();
}
```

### User-Facing Error Messages

The frontend should map error codes to user-friendly messages:

```typescript
const ERROR_MESSAGES: Record<string, string> = {
  VALIDATION_ERROR: "Please check your input and try again.",
  TEXT_EMPTY: "Please enter some text before generating.",
  INVALID_PROVIDER: "The selected provider is not available.",
  PROVIDER_NOT_CONFIGURED: "Please configure the API key for this provider in Settings.",
  PROVIDER_AUTH_ERROR: "Authentication failed. Please check your API key in Settings.",
  PROVIDER_API_ERROR: "The TTS provider returned an error. Please try again.",
  PROVIDER_RATE_LIMIT: "Rate limit exceeded. Please wait a moment and try again.",
  JOB_NOT_FOUND: "The generation job was not found. Please try generating again.",
  AUDIO_PROCESSING_ERROR: "Audio processing failed. Please try again.",
  INTERNAL_ERROR: "An unexpected error occurred. Please try again.",
  POLLING_ERROR: "Lost connection while checking generation status.",
  LOAD_ERROR: "Failed to connect to the server. Is the backend running?",
  VOICES_ERROR: "Failed to load voices for this provider.",
};

function getUserMessage(code: string, serverMessage?: string): string {
  return ERROR_MESSAGES[code] || serverMessage || "An unexpected error occurred.";
}
```

### Error Display Component

Errors should be displayed as a dismissible banner/toast at the top of the
right panel:

```typescript
interface ErrorBannerProps {
  error: { code: string; message: string } | null;
  onDismiss: () => void;
}
```

**Styling:**
- Background: dark red (`#5a1a1a`)
- Text: light red/white
- Dismiss button: X icon on the right
- Auto-dismiss after 10 seconds for non-critical errors

## Security in Error Handling

**CRITICAL (NFR-004):**

1. Backend error messages must NEVER contain API keys or credentials
2. The `details` field must NEVER contain API keys
3. The unhandled exception handler must NEVER expose stack traces to the client
4. Provider SDK error messages should be sanitized before including in the
   error response (some SDKs include request details in error messages)

**Sanitization pattern:**

```python
def sanitize_provider_error(raw_message: str) -> str:
    """
    Remove any potentially sensitive information from provider error messages.
    """
    # Remove anything that looks like an API key
    import re
    sanitized = re.sub(r'[A-Za-z0-9_\-]{20,}', '[REDACTED]', raw_message)
    # Remove URLs with query parameters (may contain keys)
    sanitized = re.sub(r'https?://\S+', '[URL REDACTED]', sanitized)
    return sanitized
```

## Notes for Developer

1. Every `except` block in provider code must catch specific SDK exceptions
   and re-raise as the appropriate `ProviderError` subclass. Never let raw
   exceptions propagate.
2. Write tests that verify error responses:
   - Correct HTTP status code
   - Correct error_code in the response body
   - No API keys or credentials in the response
   - Stack traces never exposed
3. The unhandled exception handler is a safety net. Log the full exception
   server-side but return a generic message to the client.
4. Test the error hierarchy: verify all error subclasses are caught by the
   `AppError` handler.
5. Frontend tests should verify that `ApiClientError` is thrown with the
   correct code and message for various HTTP error responses.
6. The `sanitize_provider_error` function should be tested with strings
   containing fake API keys and URLs to verify they are properly redacted.
