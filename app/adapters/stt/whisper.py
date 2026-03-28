import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.config import STT_TIMEOUT

# Thread-safe executor for Whisper transcription
_whisper_executor: ThreadPoolExecutor | None = None


def get_whisper_executor() -> ThreadPoolExecutor:
    """Get or create dedicated thread pool for Whisper operations"""
    global _whisper_executor
    if _whisper_executor is None:
        # Single-thread executor to avoid race conditions with Whisper model
        _whisper_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="whisper"
        )
    return _whisper_executor


async def transcribe_audio(
    model: Any,
    audio_path: str,
    language: str,
    timeout: int = STT_TIMEOUT,
) -> dict:
    """
    Transcribe audio using Whisper model.

    Uses dedicated single-thread executor to ensure thread-safety.
    """
    loop = asyncio.get_event_loop()
    executor = get_whisper_executor()
    return await asyncio.wait_for(
        loop.run_in_executor(executor, model.transcribe, audio_path, language),
        timeout=timeout,
    )
