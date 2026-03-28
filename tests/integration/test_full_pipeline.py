"""Integration tests for ParkPartner full pipeline

Note: These tests require proper mocking of external services.
For unit tests with full mocking, see test_service.py and test_adapters.py.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.state import set_session_histories


@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before and after each test"""
    set_session_histories({})
    yield
    set_session_histories({})


@pytest.fixture
def mock_audio_data():
    """Mock audio data"""
    return b"fake audio data"


class TestAudioValidation:
    """Test audio file validation in pipeline"""

    def test_unsupported_audio_format(self):
        """Test unsupported audio format rejection"""
        from parkpartner import app

        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/process",
            files={"file": ("test.xyz", b"fake data", "audio/xyz")},
        )

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_file_too_large(self):
        """Test file size limit"""
        from parkpartner import app

        client = TestClient(app, raise_server_exceptions=False)

        large_audio = b"x" * (11 * 1024 * 1024)  # 11MB

        response = client.post(
            "/process",
            files={"file": ("test.webm", large_audio, "audio/webm")},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"]


class TestHealthAndFrontend:
    """Test basic endpoints that don't require external services"""

    def test_health_endpoint(self):
        """Test health endpoint works"""
        from parkpartner import app

        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_frontend_endpoint(self):
        """Test frontend endpoint serves HTML"""
        from parkpartner import app

        client = TestClient(app)

        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
