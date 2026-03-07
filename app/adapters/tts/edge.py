import edge_tts
import asyncio
import os


async def synthesize_speech(
    text: str, voice: str, output_path: str, timeout: int = 20
) -> str:
    communicate = edge_tts.Communicate(text, voice)
    await asyncio.wait_for(communicate.save(output_path), timeout=timeout)

    if not os.path.exists(output_path):
        raise RuntimeError(f"TTS file not created: {output_path}")

    return output_path
