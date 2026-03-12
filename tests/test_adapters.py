"""Tests for ParkPartner adapters"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.llm.ollama import call_ollama
from app.adapters.stt.whisper import transcribe_audio
from app.adapters.tts.edge import synthesize_speech


class TestWhisperAdapter:
    """Tests for Whisper STT adapter"""

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self):
        """Test successful audio transcription"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}

        result = await transcribe_audio(
            model=mock_model,
            audio_path="/tmp/test.wav",
            language="ru",
            timeout=60,
        )

        assert result == {"text": "Hello world"}
        mock_model.transcribe.assert_called_once_with("/tmp/test.wav", language="ru")

    @pytest.mark.asyncio
    async def test_transcribe_audio_timeout(self):
        """Test transcription timeout"""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            await transcribe_audio(
                model=mock_model,
                audio_path="/tmp/test.wav",
                language="ru",
                timeout=1,
            )


class TestOllamaAdapter:
    """Tests for Ollama LLM adapter"""

    @patch("app.adapters.llm.ollama.requests.post")
    def test_call_ollama_success(self, mock_post):
        """Test successful LLM call"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "Hello there!"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = call_ollama(
            messages=[{"role": "user", "content": "Hi"}],
            model="qwen2.5:3b",
            base_url="http://localhost:11434",
        )

        assert result == "Hello there!"
        mock_post.assert_called_once()

    @patch("app.adapters.llm.ollama.requests.post")
    def test_call_ollama_timeout(self, mock_post):
        """Test LLM timeout handling"""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            call_ollama(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen2.5:3b",
                base_url="http://localhost:11434",
            )

        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail

    @patch("app.adapters.llm.ollama.requests.post")
    def test_call_ollama_unavailable(self, mock_post):
        """Test LLM unavailable handling"""
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            call_ollama(
                messages=[{"role": "user", "content": "Hi"}],
                model="qwen2.5:3b",
                base_url="http://localhost:11434",
            )

        assert exc_info.value.status_code == 502
        assert "unavailable" in exc_info.value.detail


class TestEdgeTTSAdapter:
    """Tests for Edge TTS adapter"""

    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self):
        """Test successful speech synthesis"""
        mock_communicate = AsyncMock()
        mock_communicate.save = AsyncMock()

        with patch(
            "app.adapters.tts.edge.edge_tts.Communicate", return_value=mock_communicate
        ):
            with patch("os.path.exists", return_value=True):
                result = await synthesize_speech(
                    text="Hello",
                    voice="ru-RU-DmitryNeural",
                    output_path="/tmp/test.mp3",
                    timeout=20,
                )

                assert result == "/tmp/test.mp3"
                mock_communicate.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_synthesize_speech_file_not_created(self):
        """Test error when TTS file not created"""
        mock_communicate = AsyncMock()
        mock_communicate.save = AsyncMock()

        with patch(
            "app.adapters.tts.edge.edge_tts.Communicate", return_value=mock_communicate
        ):
            with patch("os.path.exists", return_value=False):
                with pytest.raises(RuntimeError) as exc_info:
                    await synthesize_speech(
                        text="Hello",
                        voice="ru-RU-DmitryNeural",
                        output_path="/tmp/test.mp3",
                        timeout=20,
                    )

                assert "not created" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_synthesize_speech_timeout(self):
        """Test synthesis timeout"""
        mock_communicate = AsyncMock()
        mock_communicate.save = AsyncMock(side_effect=TimeoutError())

        with patch(
            "app.adapters.tts.edge.edge_tts.Communicate", return_value=mock_communicate
        ):
            with pytest.raises(asyncio.TimeoutError):
                await synthesize_speech(
                    text="Hello",
                    voice="ru-RU-DmitryNeural",
                    output_path="/tmp/test.mp3",
                    timeout=1,
                )
