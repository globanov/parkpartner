"""
System test fixtures and configuration.

System tests run against the actual application with real or stubbed external services.
"""

import logging
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Import playwright for browser fixtures
playwright = pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright

# Configure system test logging
from app.config import setup_logging

setup_logging("system", component_type="system")
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def system_config():
    """Configuration for system tests"""
    return {
        "whisper_model": "tiny",  # Faster for tests
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "tts_voice": os.getenv("TTS_VOICE", "ru-RU-DmitryNeural"),
        "max_test_duration": 30,  # seconds
    }


@pytest.fixture
def system_client():
    """
    Create TestClient for system testing.

    Note: This uses the actual application with real dependencies.
    For mocked tests, use integration test fixtures instead.
    """
    from parkpartner import app

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    client.close()


@pytest.fixture
def real_audio_file(tmp_path):
    """
    Create a temporary audio file for testing.

    Returns path to a minimal valid WebM audio file.
    In real tests, this would be an actual recorded audio file.
    """
    # Minimal WebM container with silent audio
    # This is a simplified placeholder - real tests should use actual audio
    audio_content = b"\x1a\x45\xdf\xa3\x01\x00\x00\x00\x00\x00\x00\x00"  # WebM header

    audio_path = tmp_path / "test_audio.webm"
    audio_path.write_bytes(audio_content)

    return str(audio_path)


@pytest.fixture
def clean_session():
    """
    Ensure clean session state before and after test.

    Resets session histories to empty state.
    """
    from app.core.state import get_session_histories, set_session_histories

    # Save current state
    saved_state = get_session_histories().copy()

    # Reset to clean state
    set_session_histories({})

    yield

    # Restore original state
    set_session_histories(saved_state)


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing"""
    # This would be real audio data in actual system tests
    # For now, it's a placeholder
    return b"fake_audio_data_for_testing"


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "system: mark test as a system/E2E test")
    config.addinivalue_line(
        "markers",
        "requires_services: mark test as requiring external services (Ollama, etc.)",
    )
    config.addinivalue_line("markers", "slow: mark test as slow running (>1 second)")


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test location"""
    for item in items:
        # Add system marker to all tests in system/ directory
        if "tests/system" in str(item.fspath):
            item.add_marker(pytest.mark.system)

        # Add requires_services marker to tests that need it
        if "real" in item.name.lower() or "service" in item.name.lower():
            item.add_marker(pytest.mark.requires_services)


@pytest.fixture(scope="session")
def browser_context():
    """
    Create browser context for E2E testing.

    Sets up Chromium with proper audio permissions.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
            ],
        )

        context = browser.new_context(
            viewport={"width": 375, "height": 667},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
        )

        yield context

        context.close()
        browser.close()


@pytest.fixture
def page(browser_context, base_url):
    """
    Create page for testing.

    Navigates to application and waits for load.
    """
    page = browser_context.new_page()
    page.goto(base_url, wait_until="networkidle")
    page.wait_for_selector("#recordBtn", timeout=10000)
    yield page
    page.close()
