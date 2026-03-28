import asyncio
import os

import edge_tts

from app.config import TTS_TIMEOUT

# Retry configuration for Edge TTS
TTS_MAX_RETRIES = 3
TTS_BASE_DELAY = 1.0  # seconds


async def synthesize_speech(
    text: str,
    voice: str,
    output_path: str,
    timeout: int = TTS_TIMEOUT,
) -> str:
    """
    Synthesize speech using Edge TTS with retry logic.

    Retries 2-3 times with exponential backoff on transient network errors.
    """
    communicate = edge_tts.Communicate(text, voice)

    last_error = None
    for attempt in range(TTS_MAX_RETRIES):
        try:
            await asyncio.wait_for(communicate.save(output_path), timeout=timeout)

            if os.path.exists(output_path):
                return output_path
            raise RuntimeError(f"TTS file not created: {output_path}")

        except TimeoutError:
            last_error = RuntimeError(f"TTS timeout after {timeout}s")
            if attempt < TTS_MAX_RETRIES - 1:
                delay = TTS_BASE_DELAY * (2**attempt)  # Exponential backoff
                await asyncio.sleep(delay)
        except Exception as e:
            last_error = e
            # Retry on network/transient errors
            if attempt < TTS_MAX_RETRIES - 1:
                delay = TTS_BASE_DELAY * (2**attempt)
                await asyncio.sleep(delay)
            else:
                # Last attempt failed
                raise RuntimeError(
                    f"TTS failed after {TTS_MAX_RETRIES} attempts: {e}"
                ) from e

    raise last_error
