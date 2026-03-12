from collections.abc import Callable
from dataclasses import dataclass

from app.adapters.llm.ollama import call_ollama
from app.adapters.stt.whisper import transcribe_audio
from app.adapters.tts.edge import synthesize_speech


@dataclass
class Dependencies:
    """Dependency container for adapters and config"""

    # Adapters
    stt_fn: Callable = transcribe_audio
    llm_fn: Callable = call_ollama
    tts_fn: Callable = synthesize_speech


deps = Dependencies()
