import asyncio

_session_histories: dict[str, list[dict]] = {}
_session_lock = asyncio.Lock()
_whisper_model: object = None


def get_session_histories() -> dict[str, list[dict]]:
    """Get session histories dictionary"""
    return _session_histories


def get_session_lock() -> asyncio.Lock:
    """Get session lock"""
    return _session_lock


def get_whisper_model() -> object:
    """Get loaded Whisper model"""
    return _whisper_model


def set_whisper_model(model: object) -> None:
    """Set Whisper model"""
    global _whisper_model  # noqa: PLW0603
    _whisper_model = model


def set_session_histories(histories: dict[str, list[dict]]) -> None:
    """Set session histories"""
    global _session_histories  # noqa: PLW0603
    _session_histories = histories
