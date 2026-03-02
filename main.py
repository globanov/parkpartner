import os
import logging
import traceback
import whisper
import edge_tts
import asyncio
import requests
from contextlib import asynccontextmanager
from typing import Dict, List, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,  HTMLResponse
from dotenv import load_dotenv
import tempfile

load_dotenv()

# Config
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parkpartner.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"🔍 Request: {request.method} {request.url.path} from {request.client.host}")
        response = await call_next(request)
        logger.info(f"✅ Response: {response.status_code} for {request.method} {request.url.path}")
        return response

# Global variables
whisper_model: Any = None
session_histories: Dict[str, List[dict]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model, session_histories

    logger.info("🚀 ParkPartner starting up...")
    logger.info(f"⏳ Loading Whisper model '{WHISPER_MODEL}'...")
    whisper_model = whisper.load_model(WHISPER_MODEL)
    logger.info("✅ Whisper loaded")

    session_histories = {}

    yield
    logger.info("🛑 ParkPartner shutting down...")

app = FastAPI(title="ParkPartner", version="0.1.0", lifespan=lifespan)
app.add_middleware(LogMiddleware)



# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def check_token(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "")
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

def call_ollama(messages: list, model: str = None) -> str:
    """Call local Ollama LLM"""
    if model is None:
        model = OLLAMA_MODEL

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM service timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=502, detail="LLM service unavailable")

def cleanup_files(*paths):
    """Safely delete temporary files"""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
                logger.debug(f"🗑️ Deleted: {path}")
            except Exception as e:
                logger.warning(f"Could not delete {path}: {e}")

@app.post("/process")
async def process_audio(
        file: UploadFile = File(...),
        authorization: str | None = Header(default=None),
        background_tasks: BackgroundTasks = None
):
    global session_histories

    token = check_token(authorization)
    session_id = token
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    logger.info(f"🔔 [{ts}] Request session={session_id[:8]}")

    # Validate content type
    if file.content_type not in ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"]:
        logger.warning(f"❌ Unsupported format: {file.content_type}")
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    # Read audio
    audio_data = await file.read()
    logger.debug(f"📥 [{ts}] Received {len(audio_data)} bytes, type={file.content_type}")

    if session_id not in session_histories:
        session_histories[session_id] = []
    history = session_histories[session_id]

    tmp_path = None
    tts_path = None

    try:
        # 1. Save input to temp file for Whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        logger.debug(f"💾 Temp input: {tmp_path}")

        # 2. STT: Whisper
        logger.info("🎤 Transcribing...")
        result = whisper_model.transcribe(tmp_path, language=WHISPER_LANGUAGE)  # type: ignore
        user_text = result["text"].strip()
        logger.info(f"🗣️ User: '{user_text}'")
        logger.debug(f"📝 Transcription raw: {result}")

        if not user_text:
            logger.warning("⚠️ No speech detected")
            raise HTTPException(status_code=400, detail="No speech detected")

        # 3. LLM: Ollama
        logger.info("🧠 Generating response...")
        history.append({"role": "user", "content": user_text})

        messages = [
            {"role": "system", "content": "Ты дружелюбный помощник для прогулок в парке. Отвечай кратко (1-3 предложения)."},
            *history[-6:]
        ]
        assistant_text = call_ollama(messages)
        logger.info(f"🤖 Assistant: '{assistant_text}'")

        history.append({"role": "assistant", "content": assistant_text})
        history[:] = history[-6:]

        # 4. TTS: Edge TTS
        logger.info("🗣️ Synthesizing speech...")
        tts_path = tmp_path + ".mp3"
        logger.debug(f"💾 Temp TTS output: {tts_path}")

        try:
            communicate = edge_tts.Communicate(assistant_text, "ru-RU-DmitryNeural")
            await asyncio.wait_for(communicate.save(tts_path), timeout=20.0)

            if not os.path.exists(tts_path):
                raise RuntimeError(f"TTS file not created: {tts_path}")

            file_size = os.path.getsize(tts_path)
            logger.info(f"✅ TTS saved: {tts_path} ({file_size} bytes)")

        except asyncio.TimeoutError:
            logger.error("⏰ TTS timeout")
            raise HTTPException(status_code=504, detail="TTS service timed out")
        except Exception as e:
            logger.error(f"❌ TTS error: {e}\n{traceback.format_exc()}")
            raise HTTPException(status_code=502, detail=f"TTS failed: {str(e)}")

        # 5. Schedule cleanup AFTER response is sent
        if background_tasks:
            background_tasks.add_task(cleanup_files, tmp_path, tts_path)
            logger.debug(f"🧹 Cleanup scheduled for: {tmp_path}, {tts_path}")

        # 6. Final debug summary
        logger.info(f"🎧 [{ts}] Session {session_id[:8]}: '{user_text}' → '{assistant_text}' | TTS: {tts_path}")

        # 7. Return audio
        return FileResponse(tts_path, media_type="audio/mpeg", filename="response.mp3")

    except HTTPException:
        logger.warning("⚠️ HTTPException, cleaning up...")
        cleanup_files(tmp_path, tts_path)
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}\n{traceback.format_exc()}")
        cleanup_files(tmp_path, tts_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)