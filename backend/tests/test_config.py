# TDD: Written from spec 12-configuration-and-security.md
# Tests for Settings and RuntimeConfig in backend/src/config.py

import os
import pytest


class TestSettings:
    """Tests for the Settings class (pydantic-settings based)."""

    def test_settings_default_host(self, monkeypatch):
        from src.config import Settings

        settings = Settings()
        assert settings.host == "127.0.0.1"

    def test_settings_default_port(self, monkeypatch):
        from src.config import Settings

        settings = Settings()
        assert settings.port == 8000

    def test_settings_default_audio_storage_dir(self):
        from src.config import Settings

        settings = Settings()
        assert settings.audio_storage_dir == "/tmp/tts-app-audio"

    def test_settings_loads_host_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("HOST", "0.0.0.0")
        settings = Settings()
        assert settings.host == "0.0.0.0"

    def test_settings_loads_port_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("PORT", "9000")
        settings = Settings()
        assert settings.port == 9000

    def test_settings_google_credentials_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")
        settings = Settings()
        assert settings.google_credentials_path == "/path/to/creds.json"

    def test_settings_google_credentials_default_none(self):
        from src.config import Settings

        settings = Settings()
        assert settings.google_credentials_path is None

    def test_settings_aws_credentials_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
        monkeypatch.setenv("AWS_REGION", "eu-west-1")
        settings = Settings()
        assert settings.aws_access_key_id == "AKIAIOSFODNN7EXAMPLE"
        assert settings.aws_secret_access_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert settings.aws_region == "eu-west-1"

    def test_settings_aws_default_region(self):
        from src.config import Settings

        settings = Settings()
        assert settings.aws_region == "us-east-1"

    def test_settings_elevenlabs_key_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("ELEVENLABS_API_KEY", "el-test-key")
        settings = Settings()
        assert settings.elevenlabs_api_key == "el-test-key"

    def test_settings_openai_key_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        settings = Settings()
        assert settings.openai_api_key == "sk-test-key"

    def test_settings_all_keys_default_none(self):
        from src.config import Settings

        settings = Settings()
        assert settings.google_credentials_path is None
        assert settings.aws_access_key_id is None
        assert settings.aws_secret_access_key is None
        assert settings.elevenlabs_api_key is None
        assert settings.openai_api_key is None

    def test_settings_audio_storage_dir_from_env(self, monkeypatch):
        from src.config import Settings

        monkeypatch.setenv("AUDIO_STORAGE_DIR", "/custom/audio/dir")
        settings = Settings()
        assert settings.audio_storage_dir == "/custom/audio/dir"


class TestRuntimeConfig:
    """Tests for RuntimeConfig (mutable configuration layer)."""

    def _make_settings(self, monkeypatch, **env_vars):
        """Helper to create Settings with specific env vars."""
        for k, v in env_vars.items():
            monkeypatch.setenv(k, v)
        from src.config import Settings

        return Settings()

    def test_runtime_config_reads_base_settings(self, monkeypatch):
        from src.config import RuntimeConfig

        settings = self._make_settings(monkeypatch, OPENAI_API_KEY="sk-base")
        config = RuntimeConfig(settings)
        assert config.get_openai_api_key() == "sk-base"

    def test_runtime_config_override_takes_precedence(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(monkeypatch, OPENAI_API_KEY="sk-base")
        config = RuntimeConfig(settings)
        config.set_provider_key(ProviderName.OPENAI, "sk-override")
        assert config.get_openai_api_key() == "sk-override"

    def test_runtime_config_elevenlabs_key(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(monkeypatch, ELEVENLABS_API_KEY="el-key")
        config = RuntimeConfig(settings)
        assert config.get_elevenlabs_api_key() == "el-key"

    def test_runtime_config_google_credentials(self, monkeypatch):
        from src.config import RuntimeConfig

        settings = self._make_settings(
            monkeypatch, GOOGLE_APPLICATION_CREDENTIALS="/path/creds.json"
        )
        config = RuntimeConfig(settings)
        assert config.get_google_credentials_path() == "/path/creds.json"

    def test_runtime_config_aws_credentials(self, monkeypatch):
        from src.config import RuntimeConfig

        settings = self._make_settings(
            monkeypatch,
            AWS_ACCESS_KEY_ID="AKIA",
            AWS_SECRET_ACCESS_KEY="secret",
            AWS_REGION="us-west-2",
        )
        config = RuntimeConfig(settings)
        assert config.get_aws_access_key_id() == "AKIA"
        assert config.get_aws_secret_access_key() == "secret"
        assert config.get_aws_region() == "us-west-2"

    def test_is_provider_configured_google_true(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(
            monkeypatch, GOOGLE_APPLICATION_CREDENTIALS="/path/creds.json"
        )
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.GOOGLE) is True

    def test_is_provider_configured_google_false(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName
        from src.config import Settings

        settings = Settings()
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.GOOGLE) is False

    def test_is_provider_configured_amazon_requires_both_keys(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        # Only access key, no secret
        settings = self._make_settings(monkeypatch, AWS_ACCESS_KEY_ID="AKIA")
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.AMAZON) is False

    def test_is_provider_configured_amazon_true(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(
            monkeypatch,
            AWS_ACCESS_KEY_ID="AKIA",
            AWS_SECRET_ACCESS_KEY="secret",
        )
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.AMAZON) is True

    def test_is_provider_configured_elevenlabs(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(monkeypatch, ELEVENLABS_API_KEY="key")
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.ELEVENLABS) is True

    def test_is_provider_configured_openai(self, monkeypatch):
        from src.config import RuntimeConfig
        from src.api.schemas import ProviderName

        settings = self._make_settings(monkeypatch, OPENAI_API_KEY="sk-key")
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.OPENAI) is True

    def test_is_provider_configured_after_runtime_set(self, monkeypatch):
        from src.config import RuntimeConfig, Settings
        from src.api.schemas import ProviderName

        settings = Settings()
        config = RuntimeConfig(settings)
        assert config.is_provider_configured(ProviderName.OPENAI) is False

        config.set_provider_key(ProviderName.OPENAI, "sk-new-key")
        assert config.is_provider_configured(ProviderName.OPENAI) is True

    def test_set_provider_key_google(self, monkeypatch):
        from src.config import RuntimeConfig, Settings
        from src.api.schemas import ProviderName

        settings = Settings()
        config = RuntimeConfig(settings)
        config.set_provider_key(ProviderName.GOOGLE, "/new/path.json")
        assert config.get_google_credentials_path() == "/new/path.json"

    def test_set_provider_key_elevenlabs(self, monkeypatch):
        from src.config import RuntimeConfig, Settings
        from src.api.schemas import ProviderName

        settings = Settings()
        config = RuntimeConfig(settings)
        config.set_provider_key(ProviderName.ELEVENLABS, "new-el-key")
        assert config.get_elevenlabs_api_key() == "new-el-key"
