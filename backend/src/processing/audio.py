"""
Audio stitching and file management for the TTS Reader application.

Combines multiple MP3 audio chunks into a single seamless MP3 file,
and manages temporary audio files on disk.
"""

import logging
import os
import shutil
import time
from dataclasses import dataclass
from io import BytesIO

from src.errors import AudioProcessingError

logger = logging.getLogger(__name__)


@dataclass
class StitchResult:
    """Result of stitching audio chunks together."""

    audio_bytes: bytes
    duration_ms: int
    size_bytes: int


class AudioStitcher:
    """
    Combines multiple MP3 audio chunks into a single MP3 file.

    Uses pydub for audio manipulation.
    """

    def __init__(self, crossfade_ms: int = 0, silence_between_ms: int = 100) -> None:
        """
        Args:
            crossfade_ms: Milliseconds of crossfade between chunks (0 = none).
            silence_between_ms: Milliseconds of silence to insert between
                chunks (helps with natural pacing at chunk boundaries).
        """
        self.crossfade_ms = crossfade_ms
        self.silence_between_ms = silence_between_ms

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
        from pydub import AudioSegment

        if len(audio_chunks) == 0:
            raise AudioProcessingError("No audio chunks to stitch")

        try:
            if len(audio_chunks) == 1:
                segment = AudioSegment.from_mp3(BytesIO(audio_chunks[0]))
                return self._export_as_mp3(segment)

            combined = AudioSegment.from_mp3(BytesIO(audio_chunks[0]))

            for chunk_bytes in audio_chunks[1:]:
                segment = AudioSegment.from_mp3(BytesIO(chunk_bytes))

                if self.silence_between_ms > 0:
                    silence = AudioSegment.silent(duration=self.silence_between_ms)
                    combined = combined + silence

                if self.crossfade_ms > 0:
                    combined = combined.append(segment, crossfade=self.crossfade_ms)
                else:
                    combined = combined + segment

            return self._export_as_mp3(combined)
        except AudioProcessingError:
            raise
        except Exception as exc:
            raise AudioProcessingError(str(exc)) from exc

    def get_duration_ms(self, audio_bytes: bytes) -> int:
        """
        Get the duration of an MP3 audio file in milliseconds.

        Args:
            audio_bytes: Raw MP3 data.

        Returns:
            Duration in milliseconds.

        Raises:
            AudioProcessingError: If the audio data is invalid.
        """
        from pydub import AudioSegment

        try:
            segment = AudioSegment.from_mp3(BytesIO(audio_bytes))
            return len(segment)
        except Exception as exc:
            raise AudioProcessingError(f"Cannot read audio duration: {exc}") from exc

    def _export_as_mp3(self, segment) -> StitchResult:
        """Export an AudioSegment as MP3 and return a StitchResult."""
        buffer = BytesIO()
        segment.export(buffer, format="mp3", bitrate="192k")
        audio_bytes = buffer.getvalue()
        return StitchResult(
            audio_bytes=audio_bytes,
            duration_ms=len(segment),
            size_bytes=len(audio_bytes),
        )


class AudioStore:
    """
    Manages temporary audio files on disk.

    Files are stored in a configured directory and cleaned up
    after a configurable retention period.
    """

    def __init__(self, storage_dir: str) -> None:
        """
        Args:
            storage_dir: Directory to store audio files.
                Created if it does not exist.
        """
        self._storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save(self, job_id: str, audio_bytes: bytes) -> str:
        """
        Save audio bytes to disk.

        Args:
            job_id: The job identifier (used as filename).
            audio_bytes: Raw MP3 data.

        Returns:
            Absolute file path to the saved file.
        """
        file_path = os.path.join(self._storage_dir, f"{job_id}.mp3")
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        return os.path.abspath(file_path)

    def get_path(self, job_id: str) -> str:
        """
        Get the file path for a job's audio.

        Raises:
            FileNotFoundError: If no audio file exists for this job.
        """
        file_path = os.path.join(self._storage_dir, f"{job_id}.mp3")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No audio file found for job '{job_id}'")
        return os.path.abspath(file_path)

    def delete(self, job_id: str) -> bool:
        """
        Delete the audio file for a job.

        Returns:
            True if file was deleted, False if it did not exist.
        """
        file_path = os.path.join(self._storage_dir, f"{job_id}.mp3")
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False

    def cleanup_older_than(self, hours: int) -> int:
        """
        Delete all audio files older than the specified number of hours.

        Returns:
            Number of files deleted.
        """
        cutoff = time.time() - (hours * 3600)
        removed = 0

        for filename in os.listdir(self._storage_dir):
            file_path = os.path.join(self._storage_dir, filename)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                if mtime < cutoff:
                    os.remove(file_path)
                    removed += 1

        return removed


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is installed and accessible."""
    return shutil.which("ffmpeg") is not None
