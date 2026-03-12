import hashlib
import logging
import os
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, TTS_VOICE, WHISPER_LANGUAGE
from app.core.dependencies import deps
from app.core.state import get_session_histories, get_session_lock, get_whisper_model
from app.domain.service import (
    ConversationConfig,
    ConversationDeps,
    process_conversation,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def cleanup_files(*paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
                logger.debug(f"Deleted: {path}")
            except Exception as e:
                logger.warning(f"Could not delete {path}: {e}")


@router.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


def _validate_audio_file(file: UploadFile, audio_data: bytes) -> None:
    """Validate audio file format and size"""
    valid_types = ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"]
    if file.content_type not in valid_types:
        logger.warning(f"Unsupported format: {file.content_type}")
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    if len(audio_data) > 10 * 1024 * 1024:
        logger.warning(f"File too large: {len(audio_data)} bytes")
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")


def _handle_processing_error(
    tts_path: str | None,
    error: Exception,
    status_code: int,
    message: str,
    is_warning: bool = False,
) -> None:
    """Handle processing errors with cleanup"""
    if is_warning:
        logger.warning(message)
    else:
        logger.error(message)

    if tts_path and os.path.exists(tts_path):
        cleanup_files(tts_path)

    raise HTTPException(status_code=status_code, detail=str(error)) from error


@router.post("/process")
async def process_audio(
    file: UploadFile = File(...),  # noqa: B008 - FastAPI standard pattern
    background_tasks=None,
):
    session_id = "anonymous"
    session_hash = hashlib.sha256(session_id.encode()).hexdigest()[:8]
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{ts}] Request session={session_hash}")

    audio_data = await file.read()
    _validate_audio_file(file, audio_data)

    logger.debug(f"[{ts}] Received {len(audio_data)} bytes, type={file.content_type}")

    tts_path = None
    try:
        conv_config = ConversationConfig(
            whisper_language=WHISPER_LANGUAGE,
            ollama_model=OLLAMA_MODEL,
            ollama_base_url=OLLAMA_BASE_URL,
            tts_voice=TTS_VOICE,
        )
        conv_deps = ConversationDeps(
            stt_fn=deps.stt_fn,
            llm_fn=deps.llm_fn,
            tts_fn=deps.tts_fn,
        )

        user_text, assistant_text, tts_path = await process_conversation(
            audio_data=audio_data,
            session_id=session_id,
            session_histories=get_session_histories(),
            session_lock=get_session_lock(),
            whisper_model=get_whisper_model(),
            deps=conv_deps,
            config=conv_config,
        )

        logger.info(
            f"[{ts}] Session {session_hash}: '{user_text}' -> '{assistant_text}'"
            f" | TTS: {tts_path}",
        )

        if background_tasks:
            background_tasks.add_task(cleanup_files, tts_path)
            logger.debug(f"Cleanup scheduled for: {tts_path}")

        if not os.path.exists(tts_path):
            logger.error(f"TTS file not found: {tts_path}")
            raise HTTPException(status_code=500, detail="TTS file not created")

        return FileResponse(tts_path, media_type="audio/mpeg", filename="response.mp3")

    except ValueError as e:
        _handle_processing_error(
            tts_path,
            e,
            400,
            f"No speech detected: {e}",
            is_warning=True,
        )
    except HTTPException:
        logger.warning("HTTPException, cleaning up...")
        if tts_path and os.path.exists(tts_path):
            cleanup_files(tts_path)
        raise
    except Exception as e:
        _handle_processing_error(tts_path, e, 500, f"Unexpected error: {e}")
