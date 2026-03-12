import asyncio
from typing import Any

from app.config import STT_TIMEOUT


async def transcribe_audio(
    model: Any,
    audio_path: str,
    language: str,
    timeout: int = STT_TIMEOUT,
) -> dict:
    return await asyncio.wait_for(
        asyncio.to_thread(model.transcribe, audio_path, language=language),
        timeout=timeout,
    )
