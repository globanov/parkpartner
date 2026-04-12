"""
System test fixtures and configuration.

System tests run against the actual application with real or stubbed external services.
"""

import logging
import os
from contextlib import contextmanager
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


# ── Helpers for e2e_page_with_real_audio ──────────────────────────────


def _get_test_mode(request):
    """Extract test mode from parametrize marker."""
    if hasattr(request.node, "callspec") and request.node.callspec:
        return request.node.callspec.params.get("test_mode", "localhost")
    return "localhost"


def _wait_for_server():
    """Wait for server to be healthy."""
    import time

    import requests

    for _ in range(30):
        try:
            if (
                requests.get("http://localhost:8000/health", timeout=2).status_code
                == 200
            ):
                return
        except Exception:
            time.sleep(1)


@contextmanager
def _start_tunnel():
    """Start tunnel as a proper context manager. Yields tunnel URL."""
    _wait_for_server()
    from app.utils.tunnel import TunnelManager

    with TunnelManager(port=8000) as tunnel_url:
        logger.info("Tunnel started: %s", tunnel_url)
        yield tunnel_url


def _setup_console_capture(page):
    """Attach console listener, return (log_path, messages_list)."""
    from datetime import datetime

    console_log_path = (
        Path("logs") / f"browser_console_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    console_log_path.parent.mkdir(parents=True, exist_ok=True)
    console_messages = []

    def _handle_console(msg):
        text = msg.text
        console_messages.append(text)
        with open(console_log_path, "a") as f:
            f.write(
                f"{datetime.now().strftime('%H:%M:%S.%f')[:-3]} {msg.type}: {text}\n"
            )

    page.on("console", _handle_console)
    page.on(
        "pageerror",
        lambda err: _handle_console(
            type="error", msg=type("M", (), {"text": str(err), "type": "error"})()
        ),
    )
    return console_log_path, console_messages


def _inject_audio_mock(page, audio_bytes):
    """Inject MediaRecorder mock that replaces audio with test data."""
    audio_bytes_list = list(audio_bytes)
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
                };
                return self;
            };
        })({audio_bytes_list})
        """.replace("{audio_bytes_list}", str(audio_bytes_list))
    )


def _navigate_to_app(page, target_url, timeout):
    """Navigate to app with retry logic."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            import sys

            print(f"📡 NAVIGATING TO: {target_url}", file=sys.stderr, flush=True)
            page.goto(target_url, wait_until="networkidle", timeout=timeout)
            return
        except PlaywrightTimeoutError:
            if attempt < max_attempts - 1:
                page.wait_for_timeout(2000)
            else:
                raise


def _print_console_summary(console_log_path, console_messages):
    """Print captured console messages after test."""
    print(f"\n📄 Console log saved to: {console_log_path}")
    if console_messages:
        print("\n📋 Last 20 browser console messages:")
        for msg in console_messages[-20:]:
            print(f"   {msg}")
    else:
        print("   (no console messages captured)")


# ── Main fixture ──────────────────────────────────────────────────────


def _run_e2e_page(browser_context, target_url, timeout, real_audio_bytes):
    """Common page setup and teardown for E2E tests."""
    page = browser_context.new_page()
    console_log_path, console_messages = _setup_console_capture(page)
    _inject_audio_mock(page, real_audio_bytes)
    _navigate_to_app(page, target_url, timeout)
    page.wait_for_selector("#recordBtn", timeout=10000)

    yield page
    page.close()

    _print_console_summary(console_log_path, console_messages)


@pytest.fixture
def e2e_page_with_real_audio(browser_context, request, base_url, real_audio_bytes):
    """Page with real audio, parameterized by test mode."""
    test_mode = _get_test_mode(request)

    if test_mode == "tunnel":
        with _start_tunnel() as tunnel_url:
            yield from _run_e2e_page(
                browser_context, tunnel_url, 15000, real_audio_bytes
            )
    else:
        yield from _run_e2e_page(browser_context, base_url, 10000, real_audio_bytes)
