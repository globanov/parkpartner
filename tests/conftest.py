"""
Root pytest configuration for logging.

Unifies logging format across all test types.
"""

import logging
import sys
from pathlib import Path

import pytest

from app.config import setup_logging


@pytest.fixture(autouse=True, scope="session")
def _setup_test_logging():
    """Configure logging for all tests (default: unit)"""
    setup_logging("test", component_type="unit")


@pytest.fixture(autouse=True)
def _log_test_start(request):
    """Log test start for debugging"""
    logger = logging.getLogger(__name__)
    logger.debug("Starting test: %s", request.node.nodeid)
