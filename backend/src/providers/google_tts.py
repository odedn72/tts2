"""
Google Cloud Text-to-Speech provider implementation.

Supports two authentication modes:
  1. API key (GOOGLE_API_KEY) -- REST API via httpx (preferred)
  2. Service account (GOOGLE_APPLICATION_CREDENTIALS) -- gRPC via google-cloud-texttospeech

API key takes priority when both are configured.
"""

import base64
import logging
from io import BytesIO

import httpx

from src.api.schemas import ProviderCapabilities, ProviderName, Voice, WordTiming
from src.config import RuntimeConfig
from src.errors import ProviderAPIError, ProviderAuthError, sanitize_provider_error
from src.providers.base import SynthesisResult, TTSProvider

logger = logging.getLogger(__name__)

GOOGLE_TTS_BASE_URL = "https://texttospeech.googleapis.com/v1"


class GoogleCloudTTSProvider(TTSProvider):
    """
    Google Cloud Text-to-Speech provider.

    Authentication:
      - GOOGLE_API_KEY env var (Vertex AI Express / REST API), or
      - GOOGLE_APPLICATION_CREDENTIALS env var (service account JSON file)

    Capabilities:
      - Speed control: Yes (speaking_rate parameter, 0.25-4.0)
      - Word-level timing: Yes (enable_time_pointing)
      - Max chunk: 4500 chars
      - Output format: MP3
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._voices_cache: list[Voice] | None = None
        self._http_client = httpx.AsyncClient(timeout=60.0)

    def get_provider_name(self) -> ProviderName:
        """Return the provider name enum value."""
        return ProviderName.GOOGLE

    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        return "Google Cloud TTS"

    def is_configured(self) -> bool:
        """Check if Google credentials are set (API key or service account)."""
        return bool(self._config.get_google_api_key() or self._config.get_google_credentials_path())

    def _use_rest_api(self) -> bool:
        """Return True if we should use the REST API (API key is set)."""
        return bool(self._config.get_google_api_key())

    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
            min_speed=0.25,
            max_speed=4.0,
            default_speed=1.0,
            max_chunk_chars=4500,
        )

    def _get_client(self):
        """
        Get or create the Google TTS async client (service account path).

        This is a separate method to allow easy mocking in tests.
        """
        from google.cloud import texttospeech

        credentials_path = self._config.get_google_credentials_path()
        return texttospeech.TextToSpeechAsyncClient()

    # ── REST API path (API key) ─────────────────────────────────────

    async def _rest_list_voices(self) -> list[Voice]:
        """List voices via the Google TTS REST API using an API key."""
        api_key = self._config.get_google_api_key()
        url = f"{GOOGLE_TTS_BASE_URL}/voices"

        response = await self._http_client.get(url, params={"key": api_key})

        if response.status_code in (401, 403):
            raise ProviderAuthError("google", sanitize_provider_error(response.text))
        if response.status_code != 200:
            raise ProviderAPIError("google", sanitize_provider_error(response.text))

        data = response.json()
        voices: list[Voice] = []
        for voice in data.get("voices", []):
            for lang_code in voice.get("languageCodes", []):
                voice_name = voice.get("name", "")
                voices.append(
                    Voice(
                        voice_id=voice_name,
                        name=voice_name.split("-")[-1] if "-" in voice_name else voice_name,
                        language_code=lang_code,
                        language_name=lang_code,
                        gender=voice.get("ssmlGender"),
                        provider=ProviderName.GOOGLE,
                    )
                )

        return voices

    async def _rest_synthesize(
        self, text: str, voice_id: str, speed: float
    ) -> SynthesisResult:
        """Synthesize speech via the Google TTS REST API using an API key."""
        api_key = self._config.get_google_api_key()
        url = f"{GOOGLE_TTS_BASE_URL}/text:synthesize"

        # Extract language code from voice_id (e.g. "en-US-Neural2-A" -> "en-US")
        parts = voice_id.split("-")
        if len(parts) >= 2:
            language_code = parts[0] + "-" + parts[1]
        else:
            language_code = "en-US"

        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": voice_id,
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speed,
            },
        }

        response = await self._http_client.post(url, params={"key": api_key}, json=payload)

        if response.status_code in (401, 403):
            raise ProviderAuthError("google", sanitize_provider_error(response.text))
        if response.status_code != 200:
            raise ProviderAPIError("google", sanitize_provider_error(response.text))

        data = response.json()
        audio_base64 = data.get("audioContent", "")
        audio_bytes = base64.b64decode(audio_base64) if audio_base64 else b""

        # Estimate duration from audio bytes
        duration_ms = 0
        if audio_bytes:
            try:
                from pydub import AudioSegment

                seg = AudioSegment.from_mp3(BytesIO(audio_bytes))
                duration_ms = len(seg)
            except Exception:
                duration_ms = 0

        return SynthesisResult(
            audio_bytes=audio_bytes,
            word_timings=None,
            sentence_timings=None,
            sample_rate=24000,
            duration_ms=duration_ms,
        )

    # ── Public interface ────────────────────────────────────────────

    async def list_voices(self) -> list[Voice]:
        """
        Fetch available voices from Google Cloud TTS.

        Uses REST API if API key is set, otherwise falls back to gRPC client.
        Caches results after first successful call.
        """
        if self._voices_cache is not None:
            return self._voices_cache

        if self._use_rest_api():
            voices = await self._rest_list_voices()
            self._voices_cache = voices
            return voices

        try:
            client = self._get_client()
            response = await client.list_voices()
        except Exception as exc:
            error_msg = str(exc)
            if "403" in error_msg or "Forbidden" in error_msg or "auth" in error_msg.lower():
                raise ProviderAuthError("google", sanitize_provider_error(error_msg)) from exc
            raise ProviderAPIError("google", sanitize_provider_error(error_msg)) from exc

        voices: list[Voice] = []
        for voice in response.voices:
            for lang_code in voice.language_codes:
                voices.append(
                    Voice(
                        voice_id=voice.name,
                        name=voice.name.split("-")[-1] if "-" in voice.name else voice.name,
                        language_code=lang_code,
                        language_name=lang_code,
                        gender=voice.ssml_gender.name if voice.ssml_gender else None,
                        provider=ProviderName.GOOGLE,
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
        Synthesize text to speech using Google Cloud TTS.

        Uses REST API if API key is set, otherwise falls back to gRPC client.
        Speed is clamped to the valid range (0.25-4.0).
        """
        caps = self.get_capabilities()
        speed = max(caps.min_speed, min(caps.max_speed, speed))

        if self._use_rest_api():
            return await self._rest_synthesize(text, voice_id, speed)

        from google.cloud import texttospeech

        try:
            client = self._get_client()

            synthesis_input = texttospeech.SynthesisInput(text=text)
            parts = voice_id.split("-")
            lang_code = parts[0] + "-" + parts[1] if len(parts) >= 2 else "en-US"
            voice_params = texttospeech.VoiceSelectionParams(
                language_code=lang_code,
                name=voice_id,
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speed,
            )

            response = await client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )

            audio_bytes = response.audio_content

            # Estimate duration from audio bytes
            duration_ms = 0
            if audio_bytes:
                try:
                    from pydub import AudioSegment

                    seg = AudioSegment.from_mp3(BytesIO(audio_bytes))
                    duration_ms = len(seg)
                except Exception:
                    duration_ms = 0

            # Extract timing from timepoints if available
            word_timings: list[WordTiming] = []
            if hasattr(response, "timepoints") and response.timepoints:
                words = text.split()
                char_offset = 0
                timepoints = list(response.timepoints)
                for i, tp in enumerate(timepoints):
                    word = words[i] if i < len(words) else ""
                    word_start = text.find(word, char_offset)
                    if word_start == -1:
                        word_start = char_offset
                    word_end = word_start + len(word)
                    start_ms = int(tp.time_seconds * 1000)
                    # Use next word's start as end; last word ends at audio duration
                    if i + 1 < len(timepoints):
                        end_ms = int(timepoints[i + 1].time_seconds * 1000)
                    else:
                        end_ms = duration_ms if duration_ms > 0 else start_ms + 200
                    word_timings.append(
                        WordTiming(
                            word=word,
                            start_ms=start_ms,
                            end_ms=end_ms,
                            start_char=word_start,
                            end_char=word_end,
                        )
                    )
                    char_offset = word_end

            return SynthesisResult(
                audio_bytes=audio_bytes,
                word_timings=word_timings if word_timings else None,
                sentence_timings=None,
                sample_rate=24000,
                duration_ms=duration_ms,
            )
        except (ProviderAuthError, ProviderAPIError):
            raise
        except Exception as exc:
            error_msg = sanitize_provider_error(str(exc))
            raise ProviderAPIError("google", error_msg) from exc
