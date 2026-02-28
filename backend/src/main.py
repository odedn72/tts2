"""
FastAPI application entry point with lifecycle management and error handlers.

Configures the app, registers error handlers, sets up structured logging,
request ID middleware, and graceful shutdown via SIGTERM.
"""

import asyncio
import logging
import signal
import sys

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.router import api_router
from src.config import RuntimeConfig, Settings
from src.errors import AppError, sanitize_provider_error
from src.jobs.manager import JobManager, JobStore
from src.logging_config import configure_logging
from src.middleware import RequestIDMiddleware
from src.processing.audio import AudioStitcher, AudioStore, check_ffmpeg_available
from src.processing.chunker import TextChunker
from src.processing.timing import TimingNormalizer
from src.providers.amazon_polly import AmazonPollyProvider
from src.providers.elevenlabs import ElevenLabsProvider
from src.providers.google_tts import GoogleCloudTTSProvider
from src.providers.openai_tts import OpenAITTSProvider
from src.providers.registry import ProviderRegistry

# Configure structured logging before anything else
configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup: logs that the application is ready.
    Shutdown: performs graceful cleanup (logs, cancels pending tasks).
    """
    logger.info("TTS Reader backend starting up")

    # Register SIGTERM handler for graceful shutdown in containers.
    loop = asyncio.get_running_loop()

    def _handle_sigterm():
        logger.info("Received SIGTERM, initiating graceful shutdown")
        sys.exit(0)

    if hasattr(signal, "SIGTERM"):
        loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)

    # --- Initialize all application dependencies ---

    # Configuration
    settings = Settings()
    runtime_config = RuntimeConfig(settings)

    # Check ffmpeg availability
    if not check_ffmpeg_available():
        logger.warning("ffmpeg not found — audio stitching will fail")

    # Provider registry
    registry = ProviderRegistry()
    registry.register(GoogleCloudTTSProvider(runtime_config))
    registry.register(AmazonPollyProvider(runtime_config))
    registry.register(ElevenLabsProvider(runtime_config))
    registry.register(OpenAITTSProvider(runtime_config))

    # Processing components
    chunker = TextChunker()
    timing_normalizer = TimingNormalizer()
    audio_stitcher = AudioStitcher()
    audio_store = AudioStore(settings.audio_storage_dir)

    # Job management
    job_store = JobStore()
    job_store.cleanup_old_jobs()
    job_manager = JobManager(
        provider_registry=registry,
        chunker=chunker,
        timing_normalizer=timing_normalizer,
        audio_stitcher=audio_stitcher,
        job_store=job_store,
        audio_storage_dir=settings.audio_storage_dir,
    )

    # Attach to app state for use by API endpoints
    app.state.settings = settings
    app.state.runtime_config = runtime_config
    app.state.provider_registry = registry
    app.state.job_manager = job_manager
    app.state.audio_store = audio_store

    configured = [
        p.name.value for p in registry.list_providers() if p.is_configured
    ]
    logger.info("Initialized providers: %s", configured or "none configured")
    logger.info("TTS Reader backend ready")

    yield

    # Shutdown phase
    logger.info("TTS Reader backend shutting down gracefully")


app = FastAPI(title="TTS Reader", lifespan=lifespan)

# Add request ID and timing middleware (outermost = runs first)
app.add_middleware(RequestIDMiddleware)

# Include the API router
app.include_router(api_router)

# Serve frontend static files in production (when built assets exist).
# In development, Vite dev server handles this via proxy.
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve the SPA index.html for any non-API route.

        This enables client-side routing: all paths not matched by /api/*
        or /assets/* return index.html, and the React router handles them.
        """
        file_path = (_frontend_dist / full_path).resolve()
        # Prevent path traversal attacks
        if not str(file_path).startswith(str(_frontend_dist.resolve())):
            return FileResponse(str(_frontend_dist / "index.html"))
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Handle all AppError subclasses with structured JSON responses.

    Sanitizes error messages to prevent API key leakage.
    """
    sanitized_message = sanitize_provider_error(exc.message)
    sanitized_details = exc.details
    if isinstance(sanitized_details, dict):
        sanitized_details = {
            k: sanitize_provider_error(str(v)) if isinstance(v, str) else v
            for k, v in sanitized_details.items()
        }

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error_code": exc.error_code,
            "message": sanitized_message,
            "details": sanitized_details,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unhandled exceptions with a generic error response.

    Logs the full exception for debugging but returns a safe
    generic message to the client (never exposes internals).
    """
    logger.exception("Unhandled exception")

    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": None,
        },
    )


@app.middleware("http")
async def catch_unhandled_middleware(request: Request, call_next):
    """
    Middleware to catch unhandled exceptions that bypass FastAPI's
    exception handlers (e.g., RuntimeError in newer Starlette versions).
    """
    try:
        response = await call_next(request)
        return response
    except Exception:
        logger.exception("Unhandled exception in middleware")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
            },
        )
