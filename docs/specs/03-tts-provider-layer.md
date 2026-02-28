# 03 - TTS Provider Layer

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the abstract interface for TTS providers, the provider registry, and the
implementation contract for each of the four providers: Google Cloud TTS,
Amazon Polly, ElevenLabs, and OpenAI TTS.

**MRD traceability:** FR-001 (provider selection), FR-002 (voice listing),
FR-004 (audio generation), FR-006 (word-level timing), FR-007 (sentence
fallback), FR-009 (speed control), FR-013 (capability indicators). Technical
Constraints: "each behind an abstract interface."

## Abstract Base Class

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SynthesisResult:
    """Result of synthesizing a single chunk of text."""
    audio_bytes: bytes              # Raw audio data (MP3 format)
    word_timings: list[WordTiming] | None   # Word-level timing (if supported)
    sentence_timings: list[SentenceTiming] | None  # Sentence-level timing
    sample_rate: int                # Audio sample rate in Hz
    duration_ms: int                # Duration of this chunk in milliseconds


class TTSProvider(ABC):
    """
    Abstract base class for all TTS providers.

    Each provider implementation must:
    1. Implement all abstract methods
    2. Handle its own authentication using provided config
    3. Return audio in MP3 format
    4. Return timing data in the normalized WordTiming/SentenceTiming format
    5. Raise TTSProviderError subclasses for all failures
    """

    @abstractmethod
    async def list_voices(self) -> list[Voice]:
        """
        Fetch available voices from the provider.

        Returns:
            List of Voice objects with voice_id, name, language, gender.

        Raises:
            ProviderAuthError: If credentials are invalid or missing.
            ProviderAPIError: If the API call fails.
        """
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """
        Convert a text chunk to speech.

        Args:
            text: Text to synthesize (already chunked, within provider limits).
            voice_id: The provider-specific voice identifier.
            speed: Speaking rate multiplier (1.0 = normal).

        Returns:
            SynthesisResult with audio bytes and timing data.

        Raises:
            ProviderAuthError: If credentials are invalid.
            ProviderAPIError: If synthesis fails.
            ProviderRateLimitError: If rate limited.
        """
        ...

    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """
        Return static capability metadata for this provider.

        This method is synchronous since capabilities are known statically.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check whether this provider has valid credentials configured.

        Returns True if API key / credentials are present (does not validate
        them against the API -- just checks if they are set).
        """
        ...

    @abstractmethod
    def get_provider_name(self) -> ProviderName:
        """Return the ProviderName enum value for this provider."""
        ...

    @abstractmethod
    def get_display_name(self) -> str:
        """Return a human-readable display name."""
        ...
```

## Provider Registry

```python
class ProviderRegistry:
    """
    Registry of all available TTS providers.

    Dependency injection: providers are registered at app startup.
    The registry does NOT instantiate providers -- they are passed in.
    """

    def __init__(self) -> None:
        self._providers: dict[ProviderName, TTSProvider] = {}

    def register(self, provider: TTSProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.get_provider_name()] = provider

    def get(self, name: ProviderName) -> TTSProvider:
        """
        Get a provider by name.

        Raises:
            ProviderNotFoundError: If the provider is not registered.
        """
        ...

    def list_providers(self) -> list[ProviderInfo]:
        """
        List all registered providers with their capabilities and
        configuration status.
        """
        ...

    def get_configured_providers(self) -> list[ProviderInfo]:
        """List only providers that have credentials configured."""
        ...
```

## Provider Implementations

### Google Cloud TTS

```python
class GoogleCloudTTSProvider(TTSProvider):
    """
    Google Cloud Text-to-Speech provider.

    Authentication: GOOGLE_APPLICATION_CREDENTIALS env var pointing to
    a service account JSON file.

    SDK: google-cloud-texttospeech library.

    Capabilities:
      - Speed control: Yes (speaking_rate parameter, 0.25-4.0)
      - Word-level timing: Yes (enable_time_pointing with SSML_MARK or
        timepoints in the response)
      - Max chunk: ~5000 bytes of text (use 4500 chars as safe limit)
      - Output format: MP3 supported natively

    Timing extraction:
      Google returns timepoints with `mark_name` and `time_seconds`.
      When using the timepoints feature with SSML, each word can be
      wrapped in <mark> tags. Alternatively, use the `timepoints`
      field which returns word-level data.
      Normalize to WordTiming model.

    Speed:
      Set via AudioConfig.speaking_rate (float, 0.25 to 4.0).
    """
```

**Key implementation details:**
- Use `texttospeech.TextToSpeechAsyncClient` for async operation
- Request `enable_time_pointing=["SSML_MARK"]` to get word timestamps
- Wrap text in SSML with `<mark>` tags at word boundaries for timing
- Output encoding: `texttospeech.AudioEncoding.MP3`
- Voice selection: use `voice.name` from the list_voices response as `voice_id`

### Amazon Polly

```python
class AmazonPollyProvider(TTSProvider):
    """
    Amazon Polly TTS provider.

    Authentication: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
    env vars.

    SDK: boto3 (Polly client).

    Capabilities:
      - Speed control: Yes (via SSML <prosody rate="...">)
      - Word-level timing: Yes (SpeechMarkTypes=["word"])
      - Max chunk: 3000 characters for standard voices,
        6000 for neural voices (use 2800 chars as safe limit)
      - Output format: MP3 supported

    Timing extraction:
      Use start_speech_synthesis_task with SpeechMarkTypes=["word", "sentence"]
      or synchronous synthesize_speech with OutputFormat="json" to get
      speech marks. Then make a second call for the audio.
      Polly returns speech marks as newline-delimited JSON:
        {"time":0,"type":"word","start":0,"end":5,"value":"Hello"}
      Normalize to WordTiming model.

    Speed:
      Wrap text in SSML: <speak><prosody rate="120%">text</prosody></speak>
      Convert speed float to percentage string.
    """
```

**Key implementation details:**
- Use `boto3.client("polly")` -- boto3 does not have native async, so wrap
  calls with `asyncio.to_thread()` or use `aioboto3`
- Two API calls per chunk: one for speech marks (JSON), one for audio (MP3)
- Speech marks call: `synthesize_speech(OutputFormat="json", SpeechMarkTypes=["word", "sentence"])`
- Audio call: `synthesize_speech(OutputFormat="mp3")`
- Neural voices require Engine="neural" parameter
- Voice ID is the Polly voice ID (e.g., "Joanna", "Matthew")

### ElevenLabs

```python
class ElevenLabsProvider(TTSProvider):
    """
    ElevenLabs TTS provider.

    Authentication: ELEVENLABS_API_KEY env var.

    SDK: httpx (direct REST API calls).

    Capabilities:
      - Speed control: Yes (via stability/similarity_boost/speed parameter)
      - Word-level timing: Yes (via "with_timestamps" endpoint variant)
      - Max chunk: ~5000 characters (use 4500 chars as safe limit)
      - Output format: MP3 supported

    Timing extraction:
      Use the /v1/text-to-speech/{voice_id}/with-timestamps endpoint.
      Returns alignment data with:
        { "characters": [...], "character_start_times_seconds": [...],
          "character_end_times_seconds": [...] }
      Map character-level timing to word-level by grouping characters
      between spaces. Normalize to WordTiming model.

    Speed:
      Not a direct parameter on older API versions. On newer API,
      use the `speed` parameter in the request body (0.7 to 1.2 range
      is recommended, up to 2.0 may be supported).
      If unavailable, set supports_speed_control accordingly.
    """
```

**Key implementation details:**
- Use `httpx.AsyncClient` for all API calls
- Base URL: `https://api.elevenlabs.io`
- Auth header: `xi-api-key: {api_key}`
- Voices endpoint: `GET /v1/voices`
- Synthesis with timing: `POST /v1/text-to-speech/{voice_id}/with-timestamps`
- Request body: `{ "text": "...", "model_id": "eleven_monolingual_v1", "voice_settings": {...} }`
- The response is a streaming JSON with audio base64 chunks and alignment data
- Voice ID from the voices listing

### OpenAI TTS

```python
class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS provider.

    Authentication: OPENAI_API_KEY env var.

    SDK: httpx (direct REST API calls).

    Capabilities:
      - Speed control: Yes (speed parameter, 0.25 to 4.0)
      - Word-level timing: No native support. Estimate via even
        distribution or use sentence-level fallback.
      - Max chunk: ~4096 characters (use 4000 chars as safe limit)
      - Output format: MP3 supported

    Timing extraction:
      OpenAI TTS does NOT return word-level timestamps.
      Fallback strategy:
        1. Split text into sentences
        2. Estimate sentence timing by proportional character count
           against total duration
        3. Return SentenceTiming data
      timing_type will be "sentence" for this provider.

    Speed:
      Set via `speed` parameter in request body (0.25 to 4.0).
    """
```

**Key implementation details:**
- Use `httpx.AsyncClient` for all API calls
- Endpoint: `POST https://api.openai.com/v1/audio/speech`
- Auth header: `Authorization: Bearer {api_key}`
- Request body: `{ "model": "tts-1", "input": "...", "voice": "...", "speed": 1.0, "response_format": "mp3" }`
- Available voices: alloy, echo, fable, onyx, nova, shimmer (hardcoded list,
  no dynamic listing endpoint)
- Response is raw audio bytes
- Since no timing data is returned, the provider must compute audio duration
  (e.g., by reading the MP3 header or using pydub) and then estimate sentence
  boundaries proportionally

## Provider Capability Summary

| Capability | Google Cloud TTS | Amazon Polly | ElevenLabs | OpenAI TTS |
|-----------|-----------------|--------------|------------|------------|
| `supports_speed_control` | true | true | true | true |
| `supports_word_timing` | true | true | true | false |
| `max_chunk_chars` | 4500 | 2800 | 4500 | 4000 |
| `min_speed` | 0.25 | 0.5 | 0.7 | 0.25 |
| `max_speed` | 4.0 | 2.0 | 1.2 | 4.0 |
| `default_speed` | 1.0 | 1.0 | 1.0 | 1.0 |

Note: ElevenLabs speed range may vary with API version. The developer should
verify current API docs during implementation and adjust accordingly.

## Error Handling

All provider implementations must raise errors from the error hierarchy defined
in spec 11. They must NEVER let raw SDK exceptions propagate.

```python
# Mapping of common failure modes to errors:
#
# Invalid/missing credentials -> ProviderAuthError
# API returns 4xx (not auth) -> ProviderAPIError
# API returns 429 / rate limit -> ProviderRateLimitError
# Network timeout/failure -> ProviderAPIError (with descriptive message)
# Invalid voice ID -> ProviderAPIError ("Voice not found")
# Text too long for single call -> Should not happen (chunker handles this)
```

## Dependencies

- `backend/src/providers/base.py` depends on models from `backend/src/api/schemas.py`
- `google_tts.py` depends on `google-cloud-texttospeech`
- `amazon_polly.py` depends on `boto3` (or `aioboto3`)
- `elevenlabs.py` depends on `httpx`
- `openai_tts.py` depends on `httpx`
- All implementations depend on `backend/src/config.py` for credentials
- All implementations depend on `backend/src/errors.py` for error types

## Notes for Developer

1. Each provider file should be self-contained. Import the ABC, implement it,
   and register it in the app startup.
2. Test each provider with mocked API responses. Use `respx` for httpx-based
   providers, `moto` for AWS Polly, and `unittest.mock` for the Google SDK.
3. The `list_voices` method should cache results in-memory after the first
   call to avoid repeated API calls. Use a simple instance variable.
4. For Google TTS SSML word marking: split text into words, wrap each in
   `<mark name="w{index}"/>word`, then parse timepoints from the response.
5. For Polly speech marks: the "time" field is in milliseconds, "start" and
   "end" are character byte offsets. Normalize carefully.
6. For ElevenLabs: the with-timestamps endpoint returns character-level data.
   Group characters into words by splitting on whitespace to produce
   WordTiming entries.
7. For OpenAI: since there are no timing data, compute the MP3 duration using
   pydub or mutagen, split the text into sentences, and distribute timing
   proportionally based on character count.
8. The `speed` parameter should be clamped to the provider's valid range. If
   the requested speed is outside the range, clamp it and do NOT error.
