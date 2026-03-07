import os
import logging
import traceback
import asyncio
import tempfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from app.config import SECRET_TOKEN, WHISPER_LANGUAGE, OLLAMA_BASE_URL, OLLAMA_MODEL
from app.adapters.llm.ollama import call_ollama
from app.adapters.stt.whisper import transcribe_audio
from app.adapters.tts.edge import synthesize_speech
from app.core.state import session_histories, whisper_model

logger = logging.getLogger(__name__)
router = APIRouter()


def check_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "")
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token


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
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@router.post("/process")
async def process_audio(
    file: UploadFile = File(...),
    authorization: str | None = Header(default=None),
    background_tasks: BackgroundTasks = None,
):

    token = check_token(authorization)
    session_id = token
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{ts}] Request session={session_id[:8]}")

    if file.content_type not in ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"]:
        logger.warning(f"Unsupported format: {file.content_type}")
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    audio_data = await file.read()
    logger.debug(f"[{ts}] Received {len(audio_data)} bytes, type={file.content_type}")

    if session_id not in session_histories:
        session_histories[session_id] = []
    history = session_histories[session_id]

    tmp_path = None
    tts_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
            logger.debug(f"Temp input: {tmp_path}")

        logger.info("Transcribing...")
        result = await transcribe_audio(whisper_model, tmp_path, WHISPER_LANGUAGE)
        user_text = result["text"].strip()
        logger.info(f"User: '{user_text}'")
        logger.debug(f"Transcription raw: {result}")

        if not user_text:
            logger.warning("No speech detected")
            raise HTTPException(status_code=400, detail="No speech detected")

        logger.info("Generating response...")
        history.append({"role": "user", "content": user_text})
        messages = [
            {
                "role": "system",
                "content": "Ты дружелюбный помощник для прогулок в парке. Отвечай кратко (1-3 предложения).",
            },
            *history[-6:],
        ]
        assistant_text = call_ollama(messages, OLLAMA_MODEL, OLLAMA_BASE_URL)
        logger.info(f"Assistant: '{assistant_text}'")
        history.append({"role": "assistant", "content": assistant_text})
        history[:] = history[-6:]

        logger.info("Synthesizing speech...")
        tts_path = tmp_path + ".mp3"
        logger.debug(f"Temp TTS output: {tts_path}")

        try:
            tts_path = await synthesize_speech(
                assistant_text, "ru-RU-DmitryNeural", tts_path
            )
            file_size = os.path.getsize(tts_path)
            logger.info(f"TTS saved: {tts_path} ({file_size} bytes)")
        except asyncio.TimeoutError:
            logger.error("TTS timeout")
            raise HTTPException(status_code=504, detail="TTS service timed out")
        except Exception as e:
            logger.error(f"TTS error: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=502, detail=f"TTS failed: {str(e)}")

        if background_tasks:
            background_tasks.add_task(cleanup_files, tmp_path, tts_path)
            logger.debug(f"Cleanup scheduled for: {tmp_path}, {tts_path}")

        logger.info(
            f"[{ts}] Session {session_id[:8]}: '{user_text}' -> '{assistant_text}' | TTS: {tts_path}"
        )

        return FileResponse(tts_path, media_type="audio/mpeg", filename="response.mp3")

    except HTTPException:
        logger.warning("HTTPException, cleaning up...")
        cleanup_files(tmp_path, tts_path)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
        cleanup_files(tmp_path, tts_path)
        raise HTTPException(status_code=500, detail=str(e))
