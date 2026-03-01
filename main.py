import os
import logging
import traceback
import whisper
import edge_tts
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from openai import OpenAI
import tempfile

load_dotenv()

# Config
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppState:
    """Type hints for app.state"""
    whisper_model: Any
    llm_client: OpenAI
    session_histories: Dict[str, List[dict]]

@asynccontextmanager
async def lifespan(app_l: FastAPI):
    logger.info("🚀 ParkPartner starting up...")
    logger.info(f"⏳ Loading Whisper model '{WHISPER_MODEL}'...")
    app_l.state.whisper_model = whisper.load_model(WHISPER_MODEL) # type: ignore
    logger.info("✅ Whisper loaded")

    app_l.state.llm_client = OpenAI( # type: ignore
        api_key=DASHSCOPE_API_KEY,
        base_url=DASHSCOPE_BASE_URL
    ) # type: ignore
    app_l.state.session_histories: Dict[str, List[dict]] = {} # type: ignore

    yield
    logger.info("🛑 ParkPartner shutting down...")

app = FastAPI(title="ParkPartner", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
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

@app.post("/process")
async def process_audio(
        file: UploadFile = File(...),
        authorization: str | None = Header(default=None)
):
    token = check_token(authorization)
    session_id = token

    if file.content_type not in ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    logger.info(f"📥 Received audio from session {session_id[:8]}...")

    if session_id not in app.state.session_histories: # type: ignore
        app.state.session_histories[session_id] = [] # type: ignore
    history = app.state.session_histories[session_id] # type: ignore

    tmp_path = None
    tts_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        logger.info("🎤 Transcribing...")
        result = app.state.whisper_model.transcribe(tmp_path, language=WHISPER_LANGUAGE) # type: ignore
        user_text = result["text"].strip()
        logger.info(f"🗣️ User: {user_text}")

        if not user_text:
            raise HTTPException(status_code=400, detail="No speech detected")

        logger.info("🧠 Generating response...")
        history.append({"role": "user", "content": user_text})

        response = app.state.llm_client.chat.completions.create( # type: ignore
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": "Ты дружелюбный помощник для прогулок в парке. Отвечай кратко (1-3 предложения)."},
                *history[-6:]
            ],
            max_tokens=150
        )
        assistant_text = response.choices[0].message.content.strip()
        logger.info(f"🤖 Assistant: {assistant_text}")

        history.append({"role": "assistant", "content": assistant_text})
        history[:] = history[-6:]

        logger.info("🗣️ Synthesizing speech...")
        tts_path = tmp_path + ".mp3"
        communicate = edge_tts.Communicate(assistant_text, "ru-RU-DmitryNeural")
        await asyncio.wait_for(communicate.save(tts_path), timeout=15.0)

        return FileResponse(tts_path, media_type="audio/mpeg", filename="response.mp3")

    except asyncio.TimeoutError:
        logger.error("⏰ TTS timeout")
        raise HTTPException(status_code=504, detail="TTS service timed out")
    except Exception as e:
        logger.error(f"❌ Error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for path in [tmp_path, tts_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    logger.warning(f"Could not delete {path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)