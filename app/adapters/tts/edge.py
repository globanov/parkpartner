import asyncio
import os

import edge_tts

from app.config import TTS_TIMEOUT


async def synthesize_speech(
    text: str,
    voice: str,
    output_path: str,
    timeout: int = TTS_TIMEOUT,
) -> str:
    communicate = edge_tts.Communicate(text, voice)
    await asyncio.wait_for(communicate.save(output_path), timeout=timeout)

    if not os.path.exists(output_path):
        raise RuntimeError(f"TTS file not created: {output_path}")

    return output_path
