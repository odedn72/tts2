# TDD: Shared test fixtures for all backend tests
# Written from specs 01-14

import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Ensure test environment does not load real .env files
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove provider credentials from the environment for every test."""
    for key in [
        "GOOGLE_APPLICATION_CREDENTIALS",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "ELEVENLABS_API_KEY",
        "OPENAI_API_KEY",
        "AUDIO_STORAGE_DIR",
        "HOST",
        "PORT",
    ]:
        monkeypatch.delenv(key, raising=False)


# ---------------------------------------------------------------------------
# Temporary directory for audio storage in tests
# ---------------------------------------------------------------------------
@pytest.fixture
def tmp_audio_dir(tmp_path):
    """Provide a temporary directory for audio storage."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return str(audio_dir)


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_short_text():
    return "Hello world. This is a test."


@pytest.fixture
def sample_long_text():
    """Generate a multi-paragraph text that exceeds typical chunk sizes."""
    paragraph = (
        "The quick brown fox jumps over the lazy dog. "
        "This sentence is here to add more content. "
        "Testing text-to-speech systems requires varied input. "
        "Each provider has different character limits. "
        "We need to ensure chunking works correctly.\n\n"
    )
    return paragraph * 50  # ~250 sentences, ~12500 chars


@pytest.fixture
def sample_word_timings():
    """Sample word timing data for two words."""
    return [
        {"word": "Hello", "start_ms": 0, "end_ms": 300, "start_char": 0, "end_char": 5},
        {"word": "world.", "start_ms": 300, "end_ms": 600, "start_char": 6, "end_char": 12},
    ]


@pytest.fixture
def sample_sentence_timings():
    """Sample sentence timing data."""
    return [
        {
            "sentence": "Hello world.",
            "start_ms": 0,
            "end_ms": 600,
            "start_char": 0,
            "end_char": 12,
        },
        {
            "sentence": "This is a test.",
            "start_ms": 600,
            "end_ms": 1200,
            "start_char": 13,
            "end_char": 28,
        },
    ]


@pytest.fixture
def sample_mp3_bytes():
    """Return minimal valid-ish MP3 bytes for testing (not real audio)."""
    # A minimal MP3 frame header (sync word + some bits)
    # In real tests using pydub, we would generate real audio.
    # This is a placeholder that tests can override as needed.
    return b"\xff\xfb\x90\x00" + b"\x00" * 1024
