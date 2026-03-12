import logging

import requests
from fastapi import HTTPException

from app.config import LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_TIMEOUT

logger = logging.getLogger(__name__)


def call_ollama(messages: list, model: str, base_url: str) -> str:
    """Call local Ollama LLM"""
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": LLM_TEMPERATURE,
                    "num_predict": LLM_MAX_TOKENS,
                },
            },
            timeout=LLM_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.Timeout as e:
        raise HTTPException(status_code=504, detail="LLM service timed out") from e
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=502, detail="LLM service unavailable") from e
