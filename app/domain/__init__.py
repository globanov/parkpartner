"""Domain module - core business logic"""

from .service import (
    SYSTEM_PROMPT as SYSTEM_PROMPT,
)
from .service import (
    process_conversation as process_conversation,
)

__all__ = ["SYSTEM_PROMPT", "process_conversation"]
