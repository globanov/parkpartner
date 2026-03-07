import requests
from fastapi import HTTPException
import logging

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
                "options": {"temperature": 0.7, "num_predict": 150},
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM service timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=502, detail="LLM service unavailable")
