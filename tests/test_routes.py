"""Tests for ParkPartner API routes"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing"""
    return b"fake audio data"


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check(self, client):
        """Test health endpoint returns status ok"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"


class TestFrontendEndpoint:
    """Tests for / endpoint (frontend)"""

    def test_serve_frontend(self, client):
        """Test frontend HTML is served"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"ParkPartner" in response.content


class TestProcessEndpoint:
    """Tests for /process endpoint"""

    def test_process_unsupported_format(self, client, mock_audio_data):
        """Test rejection of unsupported audio format"""
        response = client.post(
            "/process",
            files={"file": ("test.xyz", mock_audio_data, "audio/xyz")},
        )
        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_process_file_too_large(self, client):
        """Test rejection of files over 10MB"""
        large_audio = b"x" * (11 * 1024 * 1024)  # 11MB
        response = client.post(
            "/process",
            files={"file": ("test.webm", large_audio, "audio/webm")},
        )
        assert response.status_code == 413
        assert "too large" in response.json()["detail"]

    def test_process_no_speech_detected(self, client, mock_audio_data):
        """Test handling of no speech detected"""
        with patch(
            "app.adapters.api.routes.process_conversation",
            side_effect=ValueError("No speech detected"),
        ):
            response = client.post(
                "/process",
                files={"file": ("test.webm", mock_audio_data, "audio/webm")},
            )
            assert response.status_code == 400
            assert "No speech detected" in response.json()["detail"]

    def test_process_success(self, client, mock_audio_data, tmp_path):
        """Test successful audio processing"""
        mock_tts_path = tmp_path / "test_response.mp3"
        mock_tts_path.write_bytes(b"fake audio response")

        with patch(
            "app.adapters.api.routes.process_conversation",
            new_callable=AsyncMock,
        ) as mock_process:
            mock_process.return_value = (
                "Hello",
                "Hi there!",
                str(mock_tts_path),
            )

            response = client.post(
                "/process",
                files={"file": ("test.webm", mock_audio_data, "audio/webm")},
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"
