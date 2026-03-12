from typing import Protocol, runtime_checkable


@runtime_checkable
class STTPort(Protocol):
    """Speech-to-text interface"""

    async def transcribe(self, audio_path: str, language: str) -> dict: ...


@runtime_checkable
class LLMPort(Protocol):
    """Language model interface"""

    def generate(self, messages: list, model: str, base_url: str) -> str: ...


@runtime_checkable
class TTSPort(Protocol):
    """Text-to-speech interface"""

    async def synthesize(self, text: str, voice: str, output_path: str) -> str: ...
