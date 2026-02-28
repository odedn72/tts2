# TDD: Written from spec 07-audio-processing.md
# Tests for AudioStitcher and AudioStore in backend/src/processing/audio.py

import os
import time
import pytest


class TestAudioStitcher:
    """Tests for the AudioStitcher class."""

    @pytest.fixture
    def _make_mp3_bytes(self):
        """Helper to create a small valid MP3 from a pydub sine wave."""

        def _factory(duration_ms=500):
            from pydub.generators import Sine
            from io import BytesIO

            tone = Sine(440).to_audio_segment(duration=duration_ms)
            buf = BytesIO()
            tone.export(buf, format="mp3")
            return buf.getvalue()

        return _factory

    def test_stitch_empty_list_raises(self):
        from src.processing.audio import AudioStitcher
        from src.errors import AudioProcessingError

        stitcher = AudioStitcher()
        with pytest.raises(AudioProcessingError):
            stitcher.stitch([])

    def test_stitch_single_chunk(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher = AudioStitcher()
        mp3_data = _make_mp3_bytes(500)
        result = stitcher.stitch([mp3_data])
        assert result.audio_bytes is not None
        assert len(result.audio_bytes) > 0
        assert result.duration_ms > 0
        assert result.size_bytes == len(result.audio_bytes)

    def test_stitch_two_chunks(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher = AudioStitcher(silence_between_ms=0)
        chunk1 = _make_mp3_bytes(500)
        chunk2 = _make_mp3_bytes(500)
        result = stitcher.stitch([chunk1, chunk2])
        # Combined duration should be approximately the sum
        assert result.duration_ms >= 900  # Allow some tolerance

    def test_stitch_many_chunks(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher = AudioStitcher(silence_between_ms=0)
        chunks = [_make_mp3_bytes(200) for _ in range(10)]
        result = stitcher.stitch(chunks)
        assert result.duration_ms >= 1800  # 10 * 200ms with tolerance

    def test_stitch_with_silence_between(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher_no_silence = AudioStitcher(silence_between_ms=0)
        stitcher_with_silence = AudioStitcher(silence_between_ms=200)
        chunk1 = _make_mp3_bytes(500)
        chunk2 = _make_mp3_bytes(500)

        result_no = stitcher_no_silence.stitch([chunk1, chunk2])
        result_with = stitcher_with_silence.stitch([chunk1, chunk2])
        # Version with silence should be longer
        assert result_with.duration_ms > result_no.duration_ms

    def test_stitch_invalid_audio_data_raises(self):
        from src.processing.audio import AudioStitcher
        from src.errors import AudioProcessingError

        stitcher = AudioStitcher()
        with pytest.raises(AudioProcessingError):
            stitcher.stitch([b"not valid mp3 data"])

    def test_stitch_result_is_mp3(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher = AudioStitcher()
        result = stitcher.stitch([_make_mp3_bytes(300)])
        # MP3 files start with sync word 0xFF 0xFB (or similar frame header)
        # or ID3 tag header
        assert result.audio_bytes[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID") or \
               result.audio_bytes[:3] == b"ID3"


class TestAudioStitcherGetDuration:
    """Tests for getting duration of MP3 audio."""

    @pytest.fixture
    def _make_mp3_bytes(self):
        def _factory(duration_ms=500):
            from pydub.generators import Sine
            from io import BytesIO

            tone = Sine(440).to_audio_segment(duration=duration_ms)
            buf = BytesIO()
            tone.export(buf, format="mp3")
            return buf.getvalue()

        return _factory

    def test_get_duration_ms(self, _make_mp3_bytes):
        from src.processing.audio import AudioStitcher

        stitcher = AudioStitcher()
        mp3_data = _make_mp3_bytes(1000)
        duration = stitcher.get_duration_ms(mp3_data)
        # Allow tolerance for MP3 encoding
        assert abs(duration - 1000) < 100

    def test_get_duration_invalid_data_raises(self):
        from src.processing.audio import AudioStitcher
        from src.errors import AudioProcessingError

        stitcher = AudioStitcher()
        with pytest.raises(AudioProcessingError):
            stitcher.get_duration_ms(b"not valid")


class TestAudioStore:
    """Tests for the AudioStore file management class."""

    def test_audio_store_creates_directory(self, tmp_path):
        from src.processing.audio import AudioStore

        store_dir = str(tmp_path / "new_audio_dir")
        store = AudioStore(store_dir)
        assert os.path.isdir(store_dir)

    def test_save_and_get_path(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        path = store.save("job-1", b"fake mp3 data")
        assert os.path.isfile(path)
        assert path.endswith(".mp3")

        retrieved = store.get_path("job-1")
        assert retrieved == path

    def test_get_path_nonexistent_raises(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        with pytest.raises(FileNotFoundError):
            store.get_path("nonexistent-job")

    def test_delete_existing_file(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        store.save("job-1", b"data")
        result = store.delete("job-1")
        assert result is True
        with pytest.raises(FileNotFoundError):
            store.get_path("job-1")

    def test_delete_nonexistent_file(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        result = store.delete("nonexistent")
        assert result is False

    def test_cleanup_older_than(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        path = store.save("old-job", b"data")

        # Manually set the file modification time to 25 hours ago
        old_time = time.time() - (25 * 3600)
        os.utime(path, (old_time, old_time))

        removed = store.cleanup_older_than(hours=24)
        assert removed == 1

    def test_cleanup_keeps_recent_files(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        store.save("recent-job", b"data")

        removed = store.cleanup_older_than(hours=24)
        assert removed == 0

    def test_save_overwrites_existing(self, tmp_audio_dir):
        from src.processing.audio import AudioStore

        store = AudioStore(tmp_audio_dir)
        store.save("job-1", b"original data")
        store.save("job-1", b"new data")
        path = store.get_path("job-1")
        with open(path, "rb") as f:
            assert f.read() == b"new data"


class TestStitchResult:
    """Tests for the StitchResult dataclass."""

    def test_stitch_result_fields(self):
        from src.processing.audio import StitchResult

        result = StitchResult(
            audio_bytes=b"data",
            duration_ms=1000,
            size_bytes=4,
        )
        assert result.audio_bytes == b"data"
        assert result.duration_ms == 1000
        assert result.size_bytes == 4
