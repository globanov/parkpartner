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
def base_url():
    """Return base URL for tests. Fallback if pytest-base-url not provided."""
    import os

    return os.environ.get("BASE_URL", "http://localhost:8000")


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


@pytest.fixture
def e2e_page_with_real_audio(browser_context, request, base_url, real_audio_bytes):
    """Page with real audio, parameterized by test mode."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    # Get test mode from parametrize marker
    test_mode = "localhost"
    if hasattr(request.node, "callspec") and request.node.callspec:
        test_mode = request.node.callspec.params.get("test_mode", "localhost")

    # Only start tunnel for tunnel tests
    tunnel_url = None
    if test_mode == "tunnel":
        import time

        import requests

        # Wait for server
        for _ in range(30):
            try:
                if (
                    requests.get("http://localhost:8000/health", timeout=2).status_code
                    == 200
                ):
                    break
            except Exception:
                time.sleep(1)
        # Start tunnel
        from app.utils.tunnel import start_tunnel

        tunnel_url = start_tunnel(8000)
        logger.info(f"Tunnel started: {tunnel_url}")

    target_url = tunnel_url if test_mode == "tunnel" else base_url
    timeout = 15000 if test_mode == "tunnel" else 10000

    page = browser_context.new_page()
    audio_bytes_list = list(real_audio_bytes)

    page.add_init_script(
        """
        (function(audioData) {
            const OriginalMediaRecorder = window.MediaRecorder;
            window.MediaRecorder = function(stream, options) {
                const self = new OriginalMediaRecorder(stream, options);
                const originalStart = self.start.bind(self);
                const originalStop = self.stop.bind(self);
                self.start = function(timeslice) {
                    originalStart(timeslice);
                    setTimeout(() => {
                        if (self.ondataavailable) {
                            const realAudioBlob = new Blob([new Uint8Array(audioData)], { type: 'audio/webm' });
                            self.ondataavailable({ data: realAudioBlob });
                        }
                    }, 100);
                };
                self.stop = function() {
                    originalStop();
                    setTimeout(() => { if (self.onstop) self.onstop(); }, 200);
                };
                return self;
            };
        })({audio_bytes_list})
        """.replace("{audio_bytes_list}", str(audio_bytes_list))
    )

    # Retry logic for tunnel
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import sys

            print(f"📡 NAVIGATING TO: {target_url}", file=sys.stderr, flush=True)
            page.goto(target_url, wait_until="networkidle", timeout=timeout)
            break
        except PlaywrightTimeoutError:
            if attempt < max_attempts - 1:
                page.wait_for_timeout(2000)
            else:
                raise

    page.wait_for_selector("#recordBtn", timeout=10000)
    yield page
    page.close()

    # Cleanup tunnel if started
    if test_mode == "tunnel" and tunnel_url:
        from app.utils.tunnel import stop_tunnel

        stop_tunnel()
        logger.info("Tunnel stopped")
