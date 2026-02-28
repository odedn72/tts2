# 12 - Configuration and Security

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the configuration management system for API keys, server settings, and
runtime configuration.

**MRD traceability:** FR-010 (API key configuration), NFR-004 (keys not exposed
to browser), NFR-005 (localhost only).

## Configuration Loading

```python
# config.py

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Supports .env file via python-dotenv.
    """

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Audio storage
    audio_storage_dir: str = "/tmp/tts-app-audio"

    # Google Cloud TTS
    google_credentials_path: str | None = Field(
        default=None,
        alias="GOOGLE_APPLICATION_CREDENTIALS",
    )

    # Amazon Polly
    aws_access_key_id: str | None = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str | None = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")

    # ElevenLabs
    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")

    # OpenAI TTS
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
```

## Runtime Configuration Manager

The settings page allows updating API keys at runtime without restarting the
server. This requires a mutable configuration layer on top of the base settings.

```python
class RuntimeConfig:
    """
    Manages runtime-mutable configuration.

    Starts with values from Settings (environment variables).
    Can be updated via the API (FR-010).

    Thread-safe: all access is on the asyncio event loop.
    """

    def __init__(self, settings: Settings):
        self._base = settings
        self._overrides: dict[str, str] = {}

    def get_google_credentials_path(self) -> str | None:
        return self._overrides.get("google_credentials_path") or self._base.google_credentials_path

    def get_aws_access_key_id(self) -> str | None:
        return self._overrides.get("aws_access_key_id") or self._base.aws_access_key_id

    def get_aws_secret_access_key(self) -> str | None:
        return self._overrides.get("aws_secret_access_key") or self._base.aws_secret_access_key

    def get_aws_region(self) -> str:
        return self._overrides.get("aws_region") or self._base.aws_region

    def get_elevenlabs_api_key(self) -> str | None:
        return self._overrides.get("elevenlabs_api_key") or self._base.elevenlabs_api_key

    def get_openai_api_key(self) -> str | None:
        return self._overrides.get("openai_api_key") or self._base.openai_api_key

    def set_provider_key(self, provider: ProviderName, key: str) -> None:
        """
        Update an API key at runtime.

        This does NOT persist to disk -- it is session-only.
        """
        key_map = {
            ProviderName.GOOGLE: "google_credentials_path",
            ProviderName.AMAZON: "aws_access_key_id",  # Simplified
            ProviderName.ELEVENLABS: "elevenlabs_api_key",
            ProviderName.OPENAI: "openai_api_key",
        }
        field = key_map.get(provider)
        if field:
            self._overrides[field] = key

    def is_provider_configured(self, provider: ProviderName) -> bool:
        """Check if a provider has credentials set."""
        checkers = {
            ProviderName.GOOGLE: lambda: bool(self.get_google_credentials_path()),
            ProviderName.AMAZON: lambda: bool(self.get_aws_access_key_id() and self.get_aws_secret_access_key()),
            ProviderName.ELEVENLABS: lambda: bool(self.get_elevenlabs_api_key()),
            ProviderName.OPENAI: lambda: bool(self.get_openai_api_key()),
        }
        checker = checkers.get(provider)
        return checker() if checker else False
```

## Security Requirements

### NFR-004: API Keys Not Exposed to Browser

1. **Settings API response:** The `GET /api/settings` endpoint returns only
   `is_configured: true/false` for each provider. NEVER returns the actual
   key value.

2. **Error responses:** The error sanitization layer (spec 11) strips any
   values that look like API keys from error messages.

3. **Logging:** API keys must never appear in log output. Use a logging
   filter:

```python
import logging
import re

class KeyRedactingFilter(logging.Filter):
    """Redact potential API keys from log messages."""

    KEY_PATTERN = re.compile(r'[A-Za-z0-9_\-]{20,}')

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.KEY_PATTERN.sub('[REDACTED]', record.msg)
        return True
```

4. **Frontend:** The frontend never stores or displays API keys after they
   are submitted via the settings form. The password input field is cleared
   after saving.

### NFR-005: Localhost Only

```python
# main.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",  # CRITICAL: never 0.0.0.0
        port=settings.port,
        reload=True,  # For development only
    )
```

Additionally, add a startup check:

```python
@app.on_event("startup")
async def verify_localhost_binding():
    """Verify the server is bound to localhost only."""
    # This is more of a documentation/assertion than a runtime check,
    # since the binding is set in the uvicorn configuration.
    pass
```

## Application Startup

```python
# main.py

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""

    # Startup
    settings = Settings()
    runtime_config = RuntimeConfig(settings)

    # Check ffmpeg
    if not check_ffmpeg_available():
        raise RuntimeError(
            "ffmpeg is required but not found. Install it with: brew install ffmpeg"
        )

    # Create audio storage directory
    os.makedirs(settings.audio_storage_dir, exist_ok=True)

    # Initialize providers
    registry = ProviderRegistry()
    registry.register(GoogleCloudTTSProvider(runtime_config))
    registry.register(AmazonPollyProvider(runtime_config))
    registry.register(ElevenLabsProvider(runtime_config))
    registry.register(OpenAITTSProvider(runtime_config))

    # Initialize job manager
    job_store = JobStore()
    chunker = TextChunker()
    timing_normalizer = TimingNormalizer()
    audio_stitcher = AudioStitcher()
    audio_store = AudioStore(settings.audio_storage_dir)

    job_manager = JobManager(
        provider_registry=registry,
        chunker=chunker,
        timing_normalizer=timing_normalizer,
        audio_stitcher=audio_stitcher,
        job_store=job_store,
        audio_storage_dir=settings.audio_storage_dir,
    )

    # Clean up old audio files from previous sessions
    audio_store.cleanup_older_than(hours=24)

    # Store in app state for dependency injection
    app.state.provider_registry = registry
    app.state.job_manager = job_manager
    app.state.runtime_config = runtime_config
    app.state.audio_store = audio_store

    yield

    # Shutdown
    # Clean up resources if needed

app = FastAPI(title="TTS Reader", lifespan=lifespan)
```

## Dependencies

- `pydantic-settings` for Settings class
- `python-dotenv` for .env file support
- All provider modules for initialization
- Error types from spec 11

## Notes for Developer

1. Use `pydantic-settings` (separate package from pydantic v2) for the
   Settings class. It provides automatic environment variable loading.
2. The `RuntimeConfig` class enables the settings page to update keys without
   restarting. Providers should read credentials from `RuntimeConfig` on each
   API call (not cache them at initialization).
3. For AWS Polly, updating credentials at runtime is more complex since boto3
   clients cache credentials. The provider may need to recreate its client
   when credentials change.
4. Test that `Settings` loads correctly from environment variables. Use
   `monkeypatch` or `os.environ` in tests.
5. Test that `RuntimeConfig.is_provider_configured` returns the correct
   value before and after setting keys.
6. Test that the startup lifespan correctly initializes all components.
7. The `.env` file should be in `backend/.env` and should be in `.gitignore`.
   Provide a `.env.example` template.
