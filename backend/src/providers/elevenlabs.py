"""
ElevenLabs TTS provider implementation.

Uses httpx for async REST API calls to the ElevenLabs API,
with word-level timing support via the with-timestamps endpoint.
"""

import base64
import logging

import httpx

from src.api.schemas import ProviderCapabilities, ProviderName, Voice, WordTiming
from src.config import RuntimeConfig
from src.errors import (
    ProviderAPIError,
    ProviderAuthError,
    ProviderRateLimitError,
    sanitize_provider_error,
)
from src.providers.base import SynthesisResult, TTSProvider

logger = logging.getLogger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"


class ElevenLabsProvider(TTSProvider):
    """
    ElevenLabs TTS provider.

    Authentication: ELEVENLABS_API_KEY env var.

    Capabilities:
      - Speed control: Yes (speed parameter, 0.7-1.2)
      - Word-level timing: Yes (with-timestamps endpoint)
      - Max chunk: 4500 chars
      - Output format: MP3
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._voices_cache: list[Voice] | None = None
        self._client = httpx.AsyncClient(timeout=60.0)

    def get_provider_name(self) -> ProviderName:
        """Return the provider name enum value."""
        return ProviderName.ELEVENLABS

    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        return "ElevenLabs"

    def is_configured(self) -> bool:
        """Check if the ElevenLabs API key is set."""
        return bool(self._config.get_elevenlabs_api_key())

    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
            min_speed=0.7,
            max_speed=1.2,
            default_speed=1.0,
            max_chunk_chars=4500,
        )

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with the API key."""
        api_key = self._config.get_elevenlabs_api_key() or ""
        return {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

    async def list_voices(self) -> list[Voice]:
        """
        Fetch available voices from ElevenLabs.

        Caches results after first successful call.
        """
        if self._voices_cache is not None:
            return self._voices_cache

        client = self._client
        response = await client.get(
            f"{ELEVENLABS_BASE_URL}/v1/voices",
            headers=self._get_headers(),
        )

        if response.status_code == 401:
            raise ProviderAuthError("elevenlabs")
        if response.status_code != 200:
            raise ProviderAPIError(
                "elevenlabs",
                sanitize_provider_error(response.text),
            )

        data = response.json()
        voices: list[Voice] = []

        for voice_data in data.get("voices", []):
            labels = voice_data.get("labels", {})
            language = labels.get("language", "en")
            accent = labels.get("accent", "")
            language_name = f"{language}"
            if accent:
                language_name += f" ({accent})"

            voices.append(
                Voice(
                    voice_id=voice_data["voice_id"],
                    name=voice_data.get("name", voice_data["voice_id"]),
                    language_code=language,
                    language_name=language_name,
                    gender=labels.get("gender"),
                    provider=ProviderName.ELEVENLABS,
                )
            )

        self._voices_cache = voices
        return voices

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Synthesize text using the ElevenLabs with-timestamps endpoint.

        Speed is clamped to 0.7-1.2 range.
        """
        caps = self.get_capabilities()
        speed = max(caps.min_speed, min(caps.max_speed, speed))

        url = f"{ELEVENLABS_BASE_URL}/v1/text-to-speech/{voice_id}/with-timestamps"
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "speed": speed,
            },
        }

        client = self._client
        response = await client.post(
            url,
            headers=self._get_headers(),
            json=payload,
        )

        if response.status_code == 401:
            raise ProviderAuthError("elevenlabs")
        if response.status_code == 429:
            raise ProviderRateLimitError("elevenlabs")
        if response.status_code != 200:
            raise ProviderAPIError(
                "elevenlabs",
                sanitize_provider_error(response.text),
            )

        data = response.json()

        # Decode audio from base64
        audio_base64 = data.get("audio_base64", "")
        audio_bytes = base64.b64decode(audio_base64) if audio_base64 else b""

        # Extract word-level timing from character alignment
        word_timings = self._extract_word_timings(text, data.get("alignment", {}))

        # Estimate duration
        duration_ms = 0
        if word_timings:
            duration_ms = max(wt.end_ms for wt in word_timings) if word_timings else 0
        elif audio_bytes:
            try:
                from pydub import AudioSegment
                from io import BytesIO

                seg = AudioSegment.from_mp3(BytesIO(audio_bytes))
                duration_ms = len(seg)
            except Exception:
                duration_ms = 0

        return SynthesisResult(
            audio_bytes=audio_bytes,
            word_timings=word_timings if word_timings else None,
            sentence_timings=None,
            sample_rate=44100,
            duration_ms=duration_ms,
        )

    def _extract_word_timings(
        self, text: str, alignment: dict
    ) -> list[WordTiming]:
        """
        Convert character-level alignment data to word-level timing.

        Groups characters into words by splitting on whitespace.
        """
        characters = alignment.get("characters", [])
        start_times = alignment.get("character_start_times_seconds", [])
        end_times = alignment.get("character_end_times_seconds", [])

        if not characters or not start_times or not end_times:
            return []

        # Group characters into words
        word_timings: list[WordTiming] = []
        current_word = ""
        word_start_time: float | None = None
        word_end_time: float = 0.0
        word_start_char = 0
        text_offset = 0

        for i, char in enumerate(characters):
            if i >= len(start_times) or i >= len(end_times):
                break

            if char == " " or char == "\n":
                if current_word:
                    word_timings.append(
                        WordTiming(
                            word=current_word,
                            start_ms=int(word_start_time * 1000) if word_start_time else 0,
                            end_ms=int(word_end_time * 1000),
                            start_char=word_start_char,
                            end_char=word_start_char + len(current_word),
                        )
                    )
                    current_word = ""
                    word_start_time = None
                text_offset += 1
            else:
                if not current_word:
                    word_start_time = start_times[i]
                    word_start_char = text_offset
                current_word += char
                word_end_time = end_times[i]
                text_offset += 1

        # Add the last word
        if current_word:
            word_timings.append(
                WordTiming(
                    word=current_word,
                    start_ms=int(word_start_time * 1000) if word_start_time else 0,
                    end_ms=int(word_end_time * 1000),
                    start_char=word_start_char,
                    end_char=word_start_char + len(current_word),
                )
            )

        return word_timings
