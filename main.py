import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Any

import whisper
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.adapters.api.routes import router
from app.config import WHISPER_MODEL

from app.core.state import whisper_model, session_histories

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("parkpartner.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(
            f"🔍 Request: {request.method} {request.url.path} from {request.client.host}"
        )
        response = await call_next(request)
        logger.info(
            f"✅ Response: {response.status_code} for {request.method} {request.url.path}"
        )
        return response





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
app.include_router(router)
app.add_middleware(LogMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
