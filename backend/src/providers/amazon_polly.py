"""
Amazon Polly TTS provider implementation.

Uses boto3 for synchronous Polly API calls, wrapped in asyncio.to_thread
for async compatibility. Supports word-level timing via speech marks.
"""

import asyncio
import json
import logging

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


class AmazonPollyProvider(TTSProvider):
    """
    Amazon Polly TTS provider.

    Authentication: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION env vars.

    Capabilities:
      - Speed control: Yes (via SSML prosody rate)
      - Word-level timing: Yes (SpeechMarkTypes=["word"])
      - Max chunk: 2800 chars
      - Output format: MP3
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._voices_cache: list[Voice] | None = None

    def get_provider_name(self) -> ProviderName:
        """Return the provider name enum value."""
        return ProviderName.AMAZON

    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        return "Amazon Polly"

    def is_configured(self) -> bool:
        """Check if AWS credentials are set."""
        return bool(
            self._config.get_aws_access_key_id()
            and self._config.get_aws_secret_access_key()
        )

    def get_capabilities(self) -> ProviderCapabilities:
        """Return provider capabilities."""
        return ProviderCapabilities(
            supports_speed_control=True,
            supports_word_timing=True,
            min_speed=0.5,
            max_speed=2.0,
            default_speed=1.0,
            max_chunk_chars=2800,
        )

    def _get_client(self):
        """
        Get or create the boto3 Polly client.

        This is a separate method to allow easy mocking in tests.
        """
        import boto3

        return boto3.client(
            "polly",
            aws_access_key_id=self._config.get_aws_access_key_id(),
            aws_secret_access_key=self._config.get_aws_secret_access_key(),
            region_name=self._config.get_aws_region(),
        )

    async def list_voices(self) -> list[Voice]:
        """
        Fetch available voices from Amazon Polly.

        Caches results after first successful call.
        """
        if self._voices_cache is not None:
            return self._voices_cache

        try:
            client = self._get_client()
            response = await asyncio.to_thread(client.describe_voices)
        except Exception as exc:
            error_msg = str(exc)
            self._handle_boto_error(exc)
            raise ProviderAPIError("amazon", sanitize_provider_error(error_msg)) from exc

        voices: list[Voice] = []
        for voice_data in response.get("Voices", []):
            voices.append(
                Voice(
                    voice_id=voice_data["Id"],
                    name=voice_data.get("Name", voice_data["Id"]),
                    language_code=voice_data.get("LanguageCode", "en-US"),
                    language_name=voice_data.get("LanguageName", "English"),
                    gender=voice_data.get("Gender"),
                    provider=ProviderName.AMAZON,
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
        Synthesize text to speech using Amazon Polly.

        Makes two API calls: one for speech marks (timing), one for audio.
        Speed is clamped to 0.5-2.0 range and applied via SSML prosody.
        """
        caps = self.get_capabilities()
        speed = max(caps.min_speed, min(caps.max_speed, speed))

        # Wrap text in SSML for speed control
        speed_pct = int(speed * 100)
        ssml_text = f'<speak><prosody rate="{speed_pct}%">{text}</prosody></speak>'

        try:
            client = self._get_client()

            # Get speech marks (timing data)
            marks_response = await asyncio.to_thread(
                client.synthesize_speech,
                Text=ssml_text,
                TextType="ssml",
                OutputFormat="json",
                SpeechMarkTypes=["word"],
                VoiceId=voice_id,
            )

            marks_data = marks_response["AudioStream"].read().decode("utf-8")

            # Get audio
            audio_response = await asyncio.to_thread(
                client.synthesize_speech,
                Text=ssml_text,
                TextType="ssml",
                OutputFormat="mp3",
                VoiceId=voice_id,
            )

            audio_bytes = audio_response["AudioStream"].read()

            # Estimate duration from audio
            duration_ms = 0
            if audio_bytes:
                try:
                    from pydub import AudioSegment
                    from io import BytesIO

                    seg = AudioSegment.from_mp3(BytesIO(audio_bytes))
                    duration_ms = len(seg)
                except Exception:
                    duration_ms = 0

            # Parse speech marks
            # Polly returns char offsets relative to the SSML input, not
            # the original text.  Calculate the prefix length to adjust.
            ssml_prefix = ssml_text.index(text) if text in ssml_text else 0

            raw_marks: list[dict] = []
            if marks_data.strip():
                for line in marks_data.strip().split("\n"):
                    if not line.strip():
                        continue
                    try:
                        mark = json.loads(line)
                        if mark.get("type") == "word":
                            raw_marks.append(mark)
                    except (json.JSONDecodeError, KeyError):
                        continue

            word_timings: list[WordTiming] = []
            for i, mark in enumerate(raw_marks):
                start_char = mark["start"] - ssml_prefix
                end_char = mark["end"] - ssml_prefix
                start_ms = mark["time"]
                # Use next word's start as end; last word uses audio duration
                if i + 1 < len(raw_marks):
                    end_ms = raw_marks[i + 1]["time"]
                else:
                    end_ms = duration_ms if duration_ms > 0 else start_ms + 200
                word_timings.append(
                    WordTiming(
                        word=mark["value"],
                        start_ms=start_ms,
                        end_ms=end_ms,
                        start_char=max(0, start_char),
                        end_char=max(0, end_char),
                    )
                )

            return SynthesisResult(
                audio_bytes=audio_bytes,
                word_timings=word_timings if word_timings else None,
                sentence_timings=None,
                sample_rate=22050,
                duration_ms=duration_ms,
            )
        except (ProviderAuthError, ProviderAPIError, ProviderRateLimitError):
            raise
        except Exception as exc:
            self._handle_boto_error(exc)
            error_msg = sanitize_provider_error(str(exc))
            raise ProviderAPIError("amazon", error_msg) from exc

    def _handle_boto_error(self, exc: Exception) -> None:
        """
        Check if a boto3 exception should be re-raised as a specific provider error.

        Raises the appropriate provider error, or returns if unrecognized.
        """
        try:
            from botocore.exceptions import ClientError

            if isinstance(exc, ClientError):
                error_code = exc.response.get("Error", {}).get("Code", "")
                if error_code in (
                    "UnrecognizedClientException",
                    "InvalidClientTokenId",
                    "SignatureDoesNotMatch",
                    "AccessDeniedException",
                ):
                    raise ProviderAuthError(
                        "amazon", sanitize_provider_error(str(exc))
                    ) from exc
                if error_code in ("ThrottlingException", "TooManyRequestsException"):
                    raise ProviderRateLimitError("amazon") from exc
                raise ProviderAPIError(
                    "amazon", sanitize_provider_error(str(exc))
                ) from exc
        except (ProviderAuthError, ProviderAPIError, ProviderRateLimitError):
            raise
        except ImportError:
            pass
