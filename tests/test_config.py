"""Tests for ParkPartner configuration"""

import os
from unittest.mock import patch

import pytest


class TestConfigDefaults:
    """Test configuration default values"""

    @pytest.mark.parametrize(
        ("config_name", "expected_type", "expected_value"),
        [
            ("WHISPER_MODEL", str, ["small", "tiny", "base", "medium", "large"]),
            ("WHISPER_LANGUAGE", str, "ru"),
            ("OLLAMA_BASE_URL", str, "http://localhost:11434"),
            ("OLLAMA_MODEL", str, "qwen2.5:3b"),
            ("TTS_VOICE", str, "ru-RU-DmitryNeural"),
            ("MAX_HISTORY_MESSAGES", int, 6),
            ("STT_TIMEOUT", int, 60),
            ("LLM_TIMEOUT", int, 30),
            ("TTS_TIMEOUT", int, 20),
            ("LLM_TEMPERATURE", float, 0.7),
            ("LLM_MAX_TOKENS", int, 150),
        ],
    )
    def test_config_defaults(self, config_name, expected_type, expected_value):
        """Test configuration defaults"""
        import importlib

        import app.config

        importlib.reload(app.config)
        value = getattr(app.config, config_name)

        assert isinstance(value, expected_type)
        if isinstance(expected_value, list):
            assert value in expected_value
        else:
            assert value == expected_value

    def test_system_prompt_default(self):
        """Test default system prompt is in Russian"""
        from app.config import SYSTEM_PROMPT

        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 0
        assert any(ord(c) > 127 for c in SYSTEM_PROMPT)


class TestConfigFromEnvironment:
    """Test configuration loaded from environment variables"""

    @pytest.fixture(autouse=True)
    def reload_config(self):
        """Reload config module after each test"""
        import importlib

        import app.config

        yield
        importlib.reload(app.config)

    @pytest.mark.parametrize(
        ("env_var", "env_value", "config_name", "expected_value"),
        [
            ("WHISPER_MODEL", "medium", "WHISPER_MODEL", "medium"),
            ("WHISPER_LANGUAGE", "en", "WHISPER_LANGUAGE", "en"),
            (
                "OLLAMA_BASE_URL",
                "http://remote-server:11434",
                "OLLAMA_BASE_URL",
                "http://remote-server:11434",
            ),
            ("OLLAMA_MODEL", "llama3.2:3b", "OLLAMA_MODEL", "llama3.2:3b"),
            ("TTS_VOICE", "ru-RU-SvetlanaNeural", "TTS_VOICE", "ru-RU-SvetlanaNeural"),
            ("MAX_HISTORY_MESSAGES", "10", "MAX_HISTORY_MESSAGES", 10),
            ("STT_TIMEOUT", "120", "STT_TIMEOUT", 120),
            ("LLM_TIMEOUT", "60", "LLM_TIMEOUT", 60),
            ("TTS_TIMEOUT", "30", "TTS_TIMEOUT", 30),
            ("LLM_TEMPERATURE", "0.9", "LLM_TEMPERATURE", 0.9),
            ("LLM_MAX_TOKENS", "300", "LLM_MAX_TOKENS", 300),
        ],
    )
    def test_config_from_env(
        self, env_var, env_value, config_name, expected_value
    ):
        """Test configuration from environment variables"""
        import importlib

        import app.config

        with patch.dict(os.environ, {env_var: env_value}):
            importlib.reload(app.config)
            value = getattr(app.config, config_name)
            assert value == expected_value

    def test_system_prompt_from_env(self):
        """Test system prompt from environment"""
        import importlib

        import app.config

        custom_prompt = "Ты тестовый помощник."
        with patch.dict(os.environ, {"SYSTEM_PROMPT": custom_prompt}):
            importlib.reload(app.config)
            assert app.config.SYSTEM_PROMPT == custom_prompt

    @pytest.mark.parametrize(
        ("env_var", "env_value"),
        [
            ("STT_TIMEOUT", "invalid"),
            ("MAX_HISTORY_MESSAGES", "invalid"),
            ("LLM_TEMPERATURE", "not_a_number"),
        ],
    )
    def test_invalid_env_values(self, env_var, env_value):
        """Test invalid environment values raise errors"""
        import importlib

        import app.config

        with patch.dict(os.environ, {env_var: env_value}):
            with pytest.raises(ValueError):
                importlib.reload(app.config)
