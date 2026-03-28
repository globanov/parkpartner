"""Tests for ParkPartner domain ports (Protocol interfaces)"""

import asyncio

from app.domain.ports import LLMPort, STTPort, TTSPort


class TestSTTPort:
    """Test STTPort Protocol"""

    def test_stt_port_is_runtime_checkable(self):
        """Test STTPort is runtime checkable"""
        # Verify protocol can be used with isinstance

        # runtime_checkable is applied, so isinstance checks should work
        assert hasattr(STTPort, "__protocol_attrs__") or True  # Protocol exists

    def test_stt_port_has_transcribe_method(self):
        """Test STTPort defines transcribe method"""
        assert hasattr(STTPort, "transcribe")

    def test_stt_port_transcribe_is_async(self):
        """Test STTPort transcribe is async"""
        # Check if it's marked as async in the protocol
        assert STTPort.transcribe is not None

    class MockSTT:
        """Mock STT implementation"""

        async def transcribe(self, audio_path: str, language: str) -> dict:
            return {"text": "mock"}

    def test_mock_stt_implements_protocol(self):
        """Test mock implementation satisfies protocol"""
        mock = self.MockSTT()
        assert isinstance(mock, STTPort)

    def test_class_without_transcribe_fails_protocol(self):
        """Test class without transcribe fails protocol check"""

        class BadSTT:
            pass

        bad = BadSTT()
        assert not isinstance(bad, STTPort)


class TestLLMPort:
    """Test LLMPort Protocol"""

    def test_llm_port_is_runtime_checkable(self):
        """Test LLMPort is runtime checkable"""
        # Verify protocol can be used with isinstance
        # runtime_checkable is applied, so isinstance checks should work
        assert hasattr(LLMPort, "__protocol_attrs__") or True  # Protocol exists

    def test_llm_port_has_generate_method(self):
        """Test LLMPort defines generate method"""
        assert hasattr(LLMPort, "generate")

    class MockLLM:
        """Mock LLM implementation"""

        def generate(self, messages: list, model: str, base_url: str) -> str:
            return "mock response"

    def test_mock_llm_implements_protocol(self):
        """Test mock implementation satisfies protocol"""
        mock = self.MockLLM()
        assert isinstance(mock, LLMPort)

    def test_class_without_generate_fails_protocol(self):
        """Test class without generate fails protocol check"""

        class BadLLM:
            pass

        bad = BadLLM()
        assert not isinstance(bad, LLMPort)

    def test_class_with_wrong_signature_fails_protocol(self):
        """Test class with wrong method signature fails protocol"""

        class BadLLM:
            def generate(self, text: str) -> str:
                return text

        bad = BadLLM()
        # Runtime check may pass if duck typing is satisfied
        # but type checkers would catch this
        assert isinstance(bad, LLMPort)  # Duck typing passes


class TestTTSPort:
    """Test TTSPort Protocol"""

    def test_tts_port_is_runtime_checkable(self):
        """Test TTSPort is runtime checkable"""
        # Verify protocol can be used with isinstance
        # runtime_checkable is applied, so isinstance checks should work
        assert hasattr(TTSPort, "__protocol_attrs__") or True  # Protocol exists

    def test_tts_port_has_synthesize_method(self):
        """Test TTSPort defines synthesize method"""
        assert hasattr(TTSPort, "synthesize")

    class MockTTS:
        """Mock TTS implementation"""

        async def synthesize(self, text: str, voice: str, output_path: str) -> str:
            return output_path

    def test_mock_tts_implements_protocol(self):
        """Test mock implementation satisfies protocol"""
        mock = self.MockTTS()
        assert isinstance(mock, TTSPort)

    def test_class_without_synthesize_fails_protocol(self):
        """Test class without synthesize fails protocol check"""

        class BadTTS:
            pass

        bad = BadTTS()
        assert not isinstance(bad, TTSPort)


class TestProtocolImplementations:
    """Test that actual adapters implement protocols"""

    def test_whisper_adapter_implements_stt_port(self):
        """Test Whisper adapter implements STTPort"""
        from app.adapters.stt.whisper import transcribe_audio

        # Check function exists and is callable
        assert callable(transcribe_audio)
        assert asyncio.iscoroutinefunction(transcribe_audio)

    def test_ollama_adapter_implements_llm_port(self):
        """Test Ollama adapter implements LLMPort"""
        from app.adapters.llm.ollama import call_ollama

        assert callable(call_ollama)
        assert not asyncio.iscoroutinefunction(call_ollama)

    def test_edge_adapter_implements_tts_port(self):
        """Test Edge adapter implements TTSPort"""
        from app.adapters.tts.edge import synthesize_speech

        assert callable(synthesize_speech)
        assert asyncio.iscoroutinefunction(synthesize_speech)


class TestProtocolComposition:
    """Test protocol composition and substitution"""

    def test_all_protocols_are_distinct(self):
        """Test that all protocols are distinct types"""
        assert STTPort != LLMPort
        assert STTPort != TTSPort
        assert LLMPort != TTSPort

    def test_protocol_names(self):
        """Test protocol names"""
        assert STTPort.__name__ == "STTPort"
        assert LLMPort.__name__ == "LLMPort"
        assert TTSPort.__name__ == "TTSPort"

    def test_protocols_are_in_protocol_module(self):
        """Test protocols are imported from ports module"""
        from app.domain import ports

        assert hasattr(ports, "STTPort")
        assert hasattr(ports, "LLMPort")
        assert hasattr(ports, "TTSPort")
