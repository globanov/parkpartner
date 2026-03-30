"""
Integration test fixtures and configuration.

Integration tests verify interactions between components with real services.
"""

import logging

import pytest

# Configure integration test logging
from app.config import setup_logging

setup_logging("integration", component_type="integration")
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True, scope="session")
def _setup_integration_logging():
    """Configure logging for integration tests"""
    return
