"""
Configuration management for the TTS Reader application.

Loads settings from environment variables with .env file support.
Provides a RuntimeConfig layer for session-scoped API key updates.
"""

from pydantic import Field
from pydantic_settings import BaseSettings

from src.api.schemas import ProviderName


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
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")

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
        "populate_by_name": True,
    }


class RuntimeConfig:
    """
    Manages runtime-mutable configuration.

    Starts with values from Settings (environment variables).
    Can be updated via the API (FR-010).

    Thread-safe: all access is on the asyncio event loop.
    """

    def __init__(self, settings: Settings) -> None:
        self._base = settings
        self._overrides: dict[str, str] = {}

    def get_google_credentials_path(self) -> str | None:
        """Get the Google Cloud credentials file path."""
        return self._overrides.get("google_credentials_path") or self._base.google_credentials_path

    def get_google_api_key(self) -> str | None:
        """Get the Google API key (for Vertex AI Express / REST API)."""
        return self._overrides.get("google_api_key") or self._base.google_api_key

    def get_aws_access_key_id(self) -> str | None:
        """Get the AWS access key ID."""
        return self._overrides.get("aws_access_key_id") or self._base.aws_access_key_id

    def get_aws_secret_access_key(self) -> str | None:
        """Get the AWS secret access key."""
        return self._overrides.get("aws_secret_access_key") or self._base.aws_secret_access_key

    def get_aws_region(self) -> str:
        """Get the AWS region."""
        return self._overrides.get("aws_region") or self._base.aws_region

    def get_elevenlabs_api_key(self) -> str | None:
        """Get the ElevenLabs API key."""
        return self._overrides.get("elevenlabs_api_key") or self._base.elevenlabs_api_key

    def get_openai_api_key(self) -> str | None:
        """Get the OpenAI API key."""
        return self._overrides.get("openai_api_key") or self._base.openai_api_key

    def set_provider_key(self, provider: ProviderName, key: str) -> None:
        """
        Update an API key at runtime.

        This does NOT persist to disk -- it is session-only.
        """
        key_map: dict[ProviderName, str] = {
            ProviderName.GOOGLE: "google_api_key",
            ProviderName.AMAZON: "aws_access_key_id",
            ProviderName.ELEVENLABS: "elevenlabs_api_key",
            ProviderName.OPENAI: "openai_api_key",
        }
        field = key_map.get(provider)
        if field:
            self._overrides[field] = key

    def is_provider_configured(self, provider: ProviderName) -> bool:
        """Check if a provider has credentials set."""
        checkers: dict[ProviderName, callable] = {
            ProviderName.GOOGLE: lambda: bool(self.get_google_credentials_path() or self.get_google_api_key()),
            ProviderName.AMAZON: lambda: bool(
                self.get_aws_access_key_id() and self.get_aws_secret_access_key()
            ),
            ProviderName.ELEVENLABS: lambda: bool(self.get_elevenlabs_api_key()),
            ProviderName.OPENAI: lambda: bool(self.get_openai_api_key()),
        }
        checker = checkers.get(provider)
        return checker() if checker else False
