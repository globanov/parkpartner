"""Tests for ParkPartner domain service"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.service import (
    SYSTEM_PROMPT,
    ConversationConfig,
    ConversationDeps,
    process_conversation,
)


@pytest.fixture
def mock_audio_data():
    """Mock audio data"""
    return b"fake audio"


@pytest.fixture
def session_histories():
    """Empty session histories"""
    return {}


@pytest.fixture
def session_lock():
    """Async lock for tests"""
    return asyncio.Lock()


@pytest.fixture
def mock_config():
    """Mock conversation config"""
    return ConversationConfig(
        whisper_language="ru",
        ollama_model="qwen2.5:3b",
        ollama_base_url="http://localhost:11434",
        tts_voice="ru-RU-DmitryNeural",
    )


@pytest.fixture
def mock_deps():
    """Mock dependencies"""
    return ConversationDeps(
        stt_fn=AsyncMock(),
        llm_fn=MagicMock(),
        tts_fn=AsyncMock(),
    )


class TestSystemPrompt:
    """Tests for system prompt configuration"""

    def test_system_prompt_exists(self):
        """Test system prompt is defined"""
        assert SYSTEM_PROMPT is not None
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_system_prompt_language(self):
        """Test system prompt is in Russian"""
        assert any(ord(c) > 127 for c in SYSTEM_PROMPT)  # Contains Cyrillic


class TestConversationConfig:
    """Tests for ConversationConfig dataclass"""

    def test_config_creation(self, mock_config):
        """Test config can be created"""
        assert mock_config.whisper_language == "ru"
        assert mock_config.ollama_model == "qwen2.5:3b"
        assert mock_config.ollama_base_url == "http://localhost:11434"
        assert mock_config.tts_voice == "ru-RU-DmitryNeural"


class TestConversationDeps:
    """Tests for ConversationDeps dataclass"""

    def test_deps_creation(self, mock_deps):
        """Test deps can be created"""
        assert mock_deps.stt_fn is not None
        assert mock_deps.llm_fn is not None
        assert mock_deps.tts_fn is not None


class TestProcessConversation:
    """Tests for process_conversation function"""

    @pytest.mark.asyncio
    async def test_empty_audio_raises_error(
        self, mock_audio_data, session_histories, session_lock, mock_config, mock_deps
    ):
        """Test that empty transcription raises ValueError"""
        mock_deps.stt_fn.return_value = {"text": ""}

        with pytest.raises(ValueError, match="No speech detected"):
            await process_conversation(
                audio_data=mock_audio_data,
                session_id="test",
                session_histories=session_histories,
                session_lock=session_lock,
                whisper_model=MagicMock(),
                deps=mock_deps,
                config=mock_config,
            )

    @pytest.mark.asyncio
    async def test_successful_conversation(
        self, mock_audio_data, session_histories, session_lock, mock_config, mock_deps
    ):
        """Test successful conversation flow"""
        mock_deps.stt_fn.return_value = {"text": "Hello"}
        mock_deps.llm_fn.return_value = "Hi there!"
        mock_deps.tts_fn.return_value = "/tmp/test.mp3"

        with patch("os.path.exists", return_value=True):
            user_text, assistant_text, tts_path = await process_conversation(
                audio_data=mock_audio_data,
                session_id="test",
                session_histories=session_histories,
                session_lock=session_lock,
                whisper_model=MagicMock(),
                deps=mock_deps,
                config=mock_config,
            )

            assert user_text == "Hello"
            assert assistant_text == "Hi there!"
            assert tts_path == "/tmp/test.mp3"

    @pytest.mark.asyncio
    async def test_session_history_updated(
        self, mock_audio_data, session_histories, session_lock, mock_config, mock_deps
    ):
        """Test that session history is updated after conversation"""
        mock_deps.stt_fn.return_value = {"text": "Hello"}
        mock_deps.llm_fn.return_value = "Hi there!"
        mock_deps.tts_fn.return_value = "/tmp/test.mp3"

        with patch("os.path.exists", return_value=True):
            await process_conversation(
                audio_data=mock_audio_data,
                session_id="test",
                session_histories=session_histories,
                session_lock=session_lock,
                whisper_model=MagicMock(),
                deps=mock_deps,
                config=mock_config,
            )

            assert "test" in session_histories
            assert len(session_histories["test"]) == 2  # user + assistant
            assert session_histories["test"][0]["role"] == "user"
            assert session_histories["test"][1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_session_history_limited(
        self, mock_audio_data, session_histories, session_lock, mock_config, mock_deps
    ):
        """Test that session history is limited to 6 messages"""
        mock_deps.stt_fn.return_value = {"text": "Hello"}
        mock_deps.llm_fn.return_value = "Hi"
        mock_deps.tts_fn.return_value = "/tmp/test.mp3"

        # Add existing history
        session_histories["test"] = [
            {"role": "user", "content": f"msg{i}"} for i in range(6)
        ]

        with patch("os.path.exists", return_value=True):
            await process_conversation(
                audio_data=mock_audio_data,
                session_id="test",
                session_histories=session_histories,
                session_lock=session_lock,
                whisper_model=MagicMock(),
                deps=mock_deps,
                config=mock_config,
            )

            # Should have max 6 messages after truncation
            assert len(session_histories["test"]) <= 6
