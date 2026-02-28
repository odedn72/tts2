# 07 - Audio Processing

**Date:** 2026-02-28
**Status:** Draft

## Goal

Define the audio stitching component that combines multiple MP3 audio chunks
into a single seamless MP3 file.

**MRD traceability:** FR-011 (chunking and reassembly into single audio file),
FR-008 (MP3 download). Risk: "Audio chunk stitching quality."

## AudioStitcher Interface

```python
from dataclasses import dataclass


@dataclass
class StitchResult:
    """Result of stitching audio chunks together."""
    audio_bytes: bytes       # Combined MP3 audio
    duration_ms: int         # Total duration in milliseconds
    size_bytes: int          # Size of the audio data


class AudioStitcher:
    """
    Combines multiple MP3 audio chunks into a single MP3 file.

    Uses pydub for audio manipulation.
    """

    def __init__(self, crossfade_ms: int = 0, silence_between_ms: int = 100):
        """
        Args:
            crossfade_ms: Milliseconds of crossfade between chunks (0 = none).
            silence_between_ms: Milliseconds of silence to insert between
                chunks (helps with natural pacing at chunk boundaries).
        """
        ...

    def stitch(self, audio_chunks: list[bytes]) -> StitchResult:
        """
        Combine multiple MP3 byte arrays into a single MP3.

        Args:
            audio_chunks: Ordered list of MP3 audio data (one per text chunk).

        Returns:
            StitchResult with the combined audio.

        Raises:
            AudioProcessingError: If any chunk is invalid or stitching fails.
        """
        ...

    def get_duration_ms(self, audio_bytes: bytes) -> int:
        """
        Get the duration of an MP3 audio file in milliseconds.

        Useful for computing timing offsets when providers do not return
        duration information.

        Args:
            audio_bytes: Raw MP3 data.

        Returns:
            Duration in milliseconds.

        Raises:
            AudioProcessingError: If the audio data is invalid.
        """
        ...
```

## Stitching Algorithm

```
function stitch(audio_chunks):
    if len(audio_chunks) == 0:
        raise AudioProcessingError("No audio chunks to stitch")

    if len(audio_chunks) == 1:
        segment = AudioSegment.from_mp3(BytesIO(audio_chunks[0]))
        return export_as_mp3(segment)

    combined = AudioSegment.from_mp3(BytesIO(audio_chunks[0]))

    for chunk_bytes in audio_chunks[1:]:
        segment = AudioSegment.from_mp3(BytesIO(chunk_bytes))

        if silence_between_ms > 0:
            silence = AudioSegment.silent(duration=silence_between_ms)
            combined = combined + silence

        if crossfade_ms > 0:
            combined = combined.append(segment, crossfade=crossfade_ms)
        else:
            combined = combined + segment

    return export_as_mp3(combined)


function export_as_mp3(segment):
    buffer = BytesIO()
    segment.export(buffer, format="mp3", bitrate="192k")
    audio_bytes = buffer.getvalue()
    return StitchResult(
        audio_bytes=audio_bytes,
        duration_ms=len(segment),  # pydub measures duration in ms
        size_bytes=len(audio_bytes),
    )
```

## Audio File Management

```python
class AudioStore:
    """
    Manages temporary audio files on disk.

    Files are stored in AUDIO_STORAGE_DIR and cleaned up after a
    configurable retention period.
    """

    def __init__(self, storage_dir: str):
        """
        Args:
            storage_dir: Directory to store audio files.
                Created if it does not exist.
        """
        ...

    def save(self, job_id: str, audio_bytes: bytes) -> str:
        """
        Save audio bytes to disk.

        Args:
            job_id: The job identifier (used as filename).
            audio_bytes: Raw MP3 data.

        Returns:
            Absolute file path to the saved file.
        """
        ...

    def get_path(self, job_id: str) -> str:
        """
        Get the file path for a job's audio.

        Raises:
            FileNotFoundError: If no audio file exists for this job.
        """
        ...

    def delete(self, job_id: str) -> bool:
        """
        Delete the audio file for a job.

        Returns:
            True if file was deleted, False if it did not exist.
        """
        ...

    def cleanup_older_than(self, hours: int) -> int:
        """
        Delete all audio files older than the specified number of hours.

        Returns:
            Number of files deleted.
        """
        ...
```

## pydub Dependency Note

pydub requires `ffmpeg` to be installed on the system for MP3 encoding/
decoding. On macOS this can be installed via `brew install ffmpeg`.

This is a runtime dependency that must be documented in the project README.
The developer should add a startup check that verifies ffmpeg is available
and reports a clear error message if it is not.

```python
def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is installed and accessible."""
    import shutil
    return shutil.which("ffmpeg") is not None
```

This check should run at application startup and raise a clear error if
ffmpeg is not found.

## Dependencies

- `pydub` for audio manipulation
- `ffmpeg` system binary (required by pydub)
- Error types from spec 11 (`AudioProcessingError`)

## Error Handling

| Error | When | Handling |
|-------|------|----------|
| `AudioProcessingError` | Invalid MP3 data, pydub failure, ffmpeg missing | Propagate to job manager, which sets job to FAILED |
| `FileNotFoundError` | Audio file deleted or not yet created | Return 404 from API |
| `IOError` | Disk write failure | Propagate as AudioProcessingError |

## Notes for Developer

1. Use `io.BytesIO` to avoid writing intermediate files. Only the final
   stitched result gets written to disk.
2. The `silence_between_ms` parameter (default 100ms) adds a brief pause
   between chunks. This helps avoid audible "jumps" where one chunk's last
   word runs into the next chunk's first word. This value may need tuning --
   make it configurable.
3. Test with:
   - Single chunk (passthrough)
   - Two chunks (basic stitching)
   - Many chunks (10+)
   - Empty chunk list (error case)
   - Invalid MP3 data in a chunk (error case)
   - Verify output duration equals sum of input durations plus silence gaps
4. For testing, generate small MP3 fixtures using pydub's tone generator
   (`Sine` wave) rather than depending on actual TTS output.
5. The `AudioStore` should create the storage directory on initialization
   if it does not exist. Use `os.makedirs(dir, exist_ok=True)`.
6. The `cleanup_older_than` method checks file modification time with
   `os.path.getmtime()` -- this is simpler than tracking creation time
   separately.
