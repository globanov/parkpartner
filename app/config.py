import os

from dotenv import load_dotenv

load_dotenv()

# STT Settings
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ru")
STT_TIMEOUT = int(os.getenv("STT_TIMEOUT", "60"))

# LLM Settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "150"))

# TTS Settings
TTS_VOICE = os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
TTS_TIMEOUT = int(os.getenv("TTS_TIMEOUT", "20"))

# Conversation Settings
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Ты дружелюбный помощник для прогулок в парке. Отвечай кратко (1-3 предложения).",
)
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "6"))
