"""
OpenAI TTS provider implementation.

Uses httpx for async REST API calls. OpenAI TTS does not provide
word-level timestamps, so sentence-level timing is estimated.
"""

import logging

import httpx

from src.api.schemas import ProviderCapabilities, ProviderName, Voice
from src.config import RuntimeConfig
from src.errors import (
    ProviderAPIError,
    ProviderAuthError,
    ProviderRateLimitError,
    sanitize_provider_error,
)
from src.providers.base import SynthesisResult, TTSProvider

logger = logging.getLogger(__name__)

OPENAI_BASE_URL = "https://api.openai.com"

# OpenAI TTS has a fixed set of voices
OPENAI_VOICES = [
    ("alloy", "Alloy"),
    ("echo", "Echo"),
    ("fable", "Fable"),
    ("onyx", "Onyx"),
    ("nova", "Nova"),
    ("shimmer", "Shimmer"),
]


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS provider.

    Authentication: OPENAI_API_KEY env var.

    Capabilities:
      - Speed control: Yes (0.25-4.0)
      - Word-level timing: No (estimated sentence-level fallback)
      - Max chunk: 4000 chars
      - Output format: MP3
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(timeout=60.0)

    def get_provider_name(self) -> ProviderName:
        """Return the provider name enum value."""
        return ProviderName.OPENAI

    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        return "OpenAI TTS"

    def is_configured(self) -> bool:
        """Check if the OpenAI API key is set."""
        return bool(self._config.get_openai_api_key())

    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=False,
            min_speed=0.25,
            max_speed=4.0,
            default_speed=1.0,
            max_chunk_chars=4000,
        )

    async def list_voices(self) -> list[Voice]:
        """
        Return the hardcoded list of OpenAI TTS voices.

        OpenAI does not have a dynamic voice listing endpoint.
        """
        return [
            Voice(
                voice_id=voice_id,
                name=display_name,
                language_code="en-US",
                language_name="English (US)",
                gender=None,
                provider=ProviderName.OPENAI,
            )
            for voice_id, display_name in OPENAI_VOICES
        ]

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize text using the OpenAI TTS API.

        Speed is clamped to 0.25-4.0. No word-level timing is available.
        """
        caps = self.get_capabilities()
        speed = max(caps.min_speed, min(caps.max_speed, speed))

        api_key = self._config.get_openai_api_key() or ""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice_id,
            "speed": speed,
            "response_format": "mp3",
        }

        client = self._client
        response = await client.post(
            f"{OPENAI_BASE_URL}/v1/audio/speech",
            headers=headers,
            json=payload,
        )

        if response.status_code == 401:
            raise ProviderAuthError("openai")
        if response.status_code == 429:
            raise ProviderRateLimitError("openai")
        if response.status_code != 200:
            raise ProviderAPIError(
                "openai",
                sanitize_provider_error(response.text),
            )

        audio_bytes = response.content

        # Estimate duration from audio bytes
        duration_ms = 0
        if audio_bytes:
            try:
                from pydub import AudioSegment
                from io import BytesIO

                seg = AudioSegment.from_mp3(BytesIO(audio_bytes))
                duration_ms = len(seg)
            except Exception:
                duration_ms = 0

        # No word-level timing from OpenAI; sentence estimation done at job level
        return SynthesisResult(
            audio_bytes=audio_bytes,
            word_timings=None,
            sentence_timings=None,
            sample_rate=24000,
            duration_ms=duration_ms,
        )
