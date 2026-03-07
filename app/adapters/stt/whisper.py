import asyncio
from typing import Any


async def transcribe_audio(
    model: Any, audio_path: str, language: str, timeout: int = 30
) -> dict:
    return await asyncio.wait_for(
        asyncio.to_thread(model.transcribe, audio_path, language=language),
        timeout=timeout,
    )
