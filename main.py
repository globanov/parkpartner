import logging
from contextlib import asynccontextmanager

import whisper
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.adapters.api.routes import router
from app.config import WHISPER_MODEL
from app.core.state import set_session_histories, set_whisper_model

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
        client = request.client.host
        method = request.method
        path = request.url.path
        logger.info("🔍 Request: %s %s from %s", method, path, client)

        response = await call_next(request)

        logger.info("✅ Response: %s for %s %s", response.status_code, method, path)
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 ParkPartner starting up...")
    logger.info("⏳ Loading Whisper model '%s'...", WHISPER_MODEL)

    set_whisper_model(whisper.load_model(WHISPER_MODEL))
    logger.info("✅ Whisper loaded")

    set_session_histories({})

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
