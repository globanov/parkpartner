import logging
import os
import sys
from datetime import datetime
from pathlib import Path

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


# =============================================================================
# Centralized Logging Configuration
# =============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
BASE_LOGS_DIR = Path(__file__).parent.parent / "logs"

# Component type to subdirectory mapping
LOG_SUBDIRS = {
    "server": "server",
    "tunnel": "tunnel",
    "system": "tests/system",
    "integration": "tests/integration",
    "unit": "tests/unit",
    "e2e": "tests/system",  # E2E tests are system tests
    "test": "tests/unit",  # Default test type is unit
}


def get_log_filepath(prefix: str, component_type: str = "unit") -> Path:
    """
    Generate log file path with standardized naming.

    Format: logs/{component_type}/{prefix}_{YYMMDD}_{HHMMSS}.log

    Args:
        prefix: Log file prefix (e.g., 'parkpartner', 'e2e', 'test')
        component_type: Type of component ('server', 'system', 'integration', 'unit')

    Returns:
        Path to log file
    """
    # Get subdirectory for component type
    subdir = LOG_SUBDIRS.get(component_type, "tests/unit")
    logs_dir = BASE_LOGS_DIR / subdir

    # Create directory if not exists
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    return logs_dir / f"{prefix}_{timestamp}.log"


def setup_logging(
    prefix: str, component_type: str = "unit", level: int = logging.INFO
) -> None:
    """
    Configure logging with unified format.

    Args:
        prefix: Log file prefix for filename
        component_type: Type of component ('server', 'system', 'integration', 'unit')
        level: Logging level (default: INFO)
    """
    log_file = get_log_filepath(prefix, component_type)

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
