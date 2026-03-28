"""Tests for ParkPartner API routes"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from parkpartner import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing"""
    # Create minimal valid WebM file (>1KB with proper header)
    # WebM header: 0x1A 0x45 0xDF 0xA3
    webm_header = bytes([0x1A, 0x45, 0xDF, 0xA3])
    # Add padding to make it >1KB
    padding = b"\x00" * 2048
    return webm_header + padding


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check(self, client):
        """Test health endpoint returns status ok"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_health_cors_headers(self, client):
        """Test CORS headers on health endpoint"""
        response = client.get("/health", headers={"Origin": "http://example.com"})

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_health_post_method_not_allowed(self, client):
        """Test health endpoint rejects POST"""
        response = client.post("/health")
        assert response.status_code == 405


class TestFrontendEndpoint:
    """Tests for / endpoint (frontend)"""

    def test_serve_frontend(self, client):
        """Test frontend HTML is served"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"ParkPartner" in response.content

    def test_frontend_is_html(self, client):
        """Test frontend response is HTML"""
        response = client.get("/")
        content = response.content.decode("utf-8")
        assert "<!DOCTYPE html>" in content or "<html" in content

    def test_frontend_mobile_friendly(self, client):
        """Test frontend has mobile viewport"""
        response = client.get("/")
        content = response.content.decode("utf-8")
        assert "viewport" in content


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
            detail = response.json()["detail"]
            assert "No speech detected" in detail or "speech detected" in detail.lower()

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

    def test_process_cors_headers(self, client, mock_audio_data):
        """Test CORS headers on process endpoint"""
        response = client.post(
            "/process",
            files={"file": ("test.webm", mock_audio_data, "audio/webm")},
            headers={"Origin": "http://example.com"},
        )
        assert "access-control-allow-origin" in response.headers

    def test_process_missing_file(self, client):
        """Test process endpoint with missing file"""
        response = client.post("/process")
        assert response.status_code == 422


class TestCleanupUtilities:
    """Test cleanup utility functions"""

    def test_cleanup_files_existing(self, tmp_path):
        """Test cleanup of existing files"""
        from app.adapters.api.routes import cleanup_files

        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        assert test_file.exists()
        cleanup_files(str(test_file))
        assert not test_file.exists()

    def test_cleanup_files_non_existing(self, tmp_path):
        """Test cleanup of non-existing files doesn't raise"""
        from app.adapters.api.routes import cleanup_files

        non_existing = tmp_path / "non_existing.txt"
        cleanup_files(str(non_existing))

    def test_cleanup_files_multiple(self, tmp_path):
        """Test cleanup of multiple files"""
        from app.adapters.api.routes import cleanup_files

        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("test1")
        file2.write_text("test2")

        cleanup_files(str(file1), str(file2))

        assert not file1.exists()
        assert not file2.exists()

    def test_cleanup_files_mixed(self, tmp_path):
        """Test cleanup with mixed existing/non-existing files"""
        from app.adapters.api.routes import cleanup_files

        file1 = tmp_path / "test1.txt"
        file1.write_text("test1")
        file2 = tmp_path / "non_existing.txt"

        cleanup_files(str(file1), str(file2))
        assert not file1.exists()


class TestValidationUtilities:
    """Test validation utility functions"""

    def _get_validate_audio_file(self):
        """Get the validation function from routes module"""
        from app.adapters.api.routes import _validate_audio_file

        return _validate_audio_file

    def _create_valid_webm_data(self, size=2048):
        """Create valid WebM data with proper header"""
        webm_header = bytes([0x1A, 0x45, 0xDF, 0xA3])
        return webm_header + (b"\x00" * (size - 4))

    @pytest.mark.parametrize(
        "content_type",
        ["audio/webm", "audio/mp4", "audio/wav", "audio/mpeg"],
    )
    def test_validate_audio_valid_types(self, content_type):
        """Test validation of valid audio types"""
        validate_fn = self._get_validate_audio_file()
        mock_file = MagicMock()
        mock_file.content_type = content_type

        validate_fn(mock_file, self._create_valid_webm_data())

    def test_validate_audio_invalid_type(self):
        """Test validation of invalid type"""
        validate_fn = self._get_validate_audio_file()
        mock_file = MagicMock()
        mock_file.content_type = "video/mp4"

        with pytest.raises(HTTPException) as exc_info:
            validate_fn(mock_file, b"fake audio")

        assert exc_info.value.status_code == 400
        assert "Unsupported" in exc_info.value.detail

    def test_validate_audio_file_too_large(self):
        """Test validation of file too large"""
        validate_fn = self._get_validate_audio_file()
        mock_file = MagicMock()
        mock_file.content_type = "audio/webm"
        large_audio = b"x" * (11 * 1024 * 1024)  # 11MB

        with pytest.raises(HTTPException) as exc_info:
            validate_fn(mock_file, large_audio)

        assert exc_info.value.status_code == 413
        assert "too large" in exc_info.value.detail

    @pytest.mark.parametrize(
        "size",
        [10 * 1024 * 1024, 10 * 1024 * 1024 - 1],  # Exactly 10MB, Just under
    )
    def test_validate_audio_file_size_boundaries(self, size):
        """Test validation of file at size boundaries"""
        validate_fn = self._get_validate_audio_file()
        mock_file = MagicMock()
        mock_file.content_type = "audio/webm"
        audio = self._create_valid_webm_data(size)

        validate_fn(mock_file, audio)


class TestErrorHandlingUtilities:
    """Test error handling utility functions"""

    def test_handle_processing_error_value_error(self, tmp_path):
        """Test handling ValueError"""
        from app.adapters.api.routes import _handle_processing_error

        tts_file = tmp_path / "test.mp3"
        tts_file.write_text("test")

        error = ValueError("Test error")

        with pytest.raises(HTTPException) as exc_info:
            _handle_processing_error(
                str(tts_file),
                error,
                400,
                "Test message",
                is_warning=True,
            )

        assert exc_info.value.status_code == 400
        assert not tts_file.exists()

    def test_handle_processing_error_no_tts_file(self):
        """Test handling error when TTS file doesn't exist"""
        from app.adapters.api.routes import _handle_processing_error

        error = ValueError("Test error")

        with pytest.raises(HTTPException):
            _handle_processing_error(
                None,
                error,
                400,
                "Test message",
            )

    def test_handle_processing_error_http_exception(self):
        """Test handling HTTPException"""
        from app.adapters.api.routes import _handle_processing_error

        error = HTTPException(status_code=500, detail="Server error")

        with pytest.raises(HTTPException) as exc_info:
            _handle_processing_error(
                None,
                error,
                500,
                "Test message",
            )

        assert exc_info.value.status_code == 500
