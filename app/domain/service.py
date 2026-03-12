import asyncio
import logging
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from app.config import MAX_HISTORY_MESSAGES, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class ConversationConfig:
    """Configuration for conversation processing"""

    whisper_language: str
    ollama_model: str
    ollama_base_url: str
    tts_voice: str


@dataclass
class ConversationDeps:
    """Dependency container for conversation processing"""

    stt_fn: Callable
    llm_fn: Callable
    tts_fn: Callable


async def process_conversation(  # noqa: PLR0913 - Pipeline function, params grouped in dataclasses
    audio_data: bytes,
    session_id: str,
    session_histories: dict[str, list[dict]],
    session_lock: asyncio.Lock,
    whisper_model,
    deps: ConversationDeps,
    config: ConversationConfig,
) -> tuple[str, str, str]:
    """
    Process audio through full conversation pipeline:
    transcribe → LLM → synthesize

    Returns: (user_text, assistant_text, tts_path)
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Transcribe
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        result = await deps.stt_fn(whisper_model, tmp_path, config.whisper_language)
        user_text = result["text"].strip()

        if not user_text:
            os.unlink(tmp_path)
            raise ValueError("No speech detected")

        logger.info(f"User: '{user_text}'")

        # Get/update history with lock
        async with session_lock:
            if session_id not in session_histories:
                session_histories[session_id] = []
            history = session_histories[session_id]

            # Build messages
            history.append({"role": "user", "content": user_text})
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                *history[-MAX_HISTORY_MESSAGES:],
            ]

            # Call LLM
            assistant_text = deps.llm_fn(
                messages,
                config.ollama_model,
                config.ollama_base_url,
            )
            logger.info(f"Assistant: '{assistant_text}'")

            # Update history
            history.append({"role": "assistant", "content": assistant_text})
            history[:] = history[-MAX_HISTORY_MESSAGES:]

        # Synthesize
        tts_path = tmp_path + ".mp3"
        tts_path = await deps.tts_fn(assistant_text, config.tts_voice, tts_path)

        logger.info(
            f"[{ts}] Session {session_id[:8]}: '{user_text}' -> '{assistant_text}'",
        )

        return user_text, assistant_text, tts_path

    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
