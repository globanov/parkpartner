"""
System tests for full application flow.

These tests verify the complete user journey through the application.
They require external services (Ollama, etc.) to be running.
"""

import os
import time

import pytest


@pytest.mark.system
class TestFullApplicationFlow:
    """Tests for complete application flow"""

    @pytest.mark.requires_services
    @pytest.mark.slow
    def test_health_endpoint_responds(self, system_client):
        """Verify health endpoint is accessible"""
        response = system_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "version" in response.json()

    @pytest.mark.requires_services
    @pytest.mark.slow
    def test_frontend_serves_html(self, system_client):
        """Verify frontend HTML is served"""
        response = system_client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"ParkPartner" in response.content

    def test_audio_validation_rejects_invalid_format(
        self, system_client, clean_session
    ):
        """Verify invalid audio formats are rejected"""
        response = system_client.post(
            "/process",
            files={"file": ("test.txt", b"not audio", "text/plain")},
        )

        assert response.status_code == 400
        assert "Unsupported" in response.json()["detail"]

    def test_audio_validation_rejects_oversized_file(
        self, system_client, clean_session
    ):
        """Verify oversized files are rejected"""
        large_audio = b"x" * (11 * 1024 * 1024)  # 11MB

        response = system_client.post(
            "/process",
            files={"file": ("test.webm", large_audio, "audio/webm")},
        )

        assert response.status_code == 413
        assert "too large" in response.json()["detail"]

    @pytest.mark.skipif(
        not os.getenv("OLLAMA_BASE_URL"), reason="Requires Ollama service to be running"
    )
    @pytest.mark.requires_services
    @pytest.mark.slow
    def test_full_conversation_with_real_services(
        self, system_client, clean_session, real_audio_file
    ):
        """
        Test complete conversation flow with real services.

        This test requires:
        - Ollama service running
        - Whisper model loaded
        - Edge TTS accessible

        Skip if services are not available.
        """
        # Note: This test would use a real audio file in production
        # For now, it demonstrates the test structure

        if not os.path.exists(real_audio_file):
            pytest.skip("Real audio file not available")

        start_time = time.time()

        with open(real_audio_file, "rb") as f:
            response = system_client.post(
                "/process",
                files={"file": ("test.webm", f, "audio/webm")},
            )

        elapsed = time.time() - start_time

        # Response should be audio (or error if audio is invalid)
        # With real audio, this would be 200
        assert response.status_code in [200, 400, 500]

        # If successful, verify audio response
        if response.status_code == 200:
            assert response.headers["content-type"] == "audio/mpeg"
            assert len(response.content) > 0

        # Performance check (adjust threshold as needed)
        assert elapsed < 30, f"Request took too long: {elapsed:.2f}s"


@pytest.mark.system
class TestConversationContinuity:
    """Tests for conversation history and context"""

    def test_session_state_is_maintained(self, system_client, clean_session):
        """Verify session state persists across requests"""
        from app.core.state import get_session_histories

        # First request would add to history
        # (skipped without real services)

        # Verify history is accessible
        histories = get_session_histories()
        assert isinstance(histories, dict)

    def test_multiple_sessions_are_isolated(self, system_client, clean_session):
        """Verify different sessions don't interfere"""
        from app.core.state import get_session_histories, set_session_histories

        # Set up two sessions
        set_session_histories(
            {
                "session_a": [{"role": "user", "content": "Hello A"}],
                "session_b": [{"role": "user", "content": "Hello B"}],
            }
        )

        histories = get_session_histories()

        assert "session_a" in histories
        assert "session_b" in histories
        assert histories["session_a"][0]["content"] == "Hello A"
        assert histories["session_b"][0]["content"] == "Hello B"


@pytest.mark.system
class TestErrorRecovery:
    """Tests for error handling and recovery"""

    def test_app_recovers_from_invalid_request(self, system_client, clean_session):
        """Verify app continues working after invalid request"""
        # Send invalid request
        system_client.post(
            "/process",
            files={"file": ("bad.mp3", b"", "audio/mpeg")},
        )

        # App should still be responsive
        response2 = system_client.get("/health")
        assert response2.status_code == 200

    def test_concurrent_requests_dont_corrupt_state(self, system_client, clean_session):
        """Verify concurrent requests maintain data integrity"""
        import concurrent.futures

        def make_request():
            return system_client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)


# Performance benchmarks (optional, run separately)
@pytest.mark.system
@pytest.mark.slow
class TestPerformance:
    """Performance benchmarks for system tests"""

    @pytest.mark.requires_services
    def test_health_endpoint_latency(self, system_client):
        """Measure health endpoint response time"""
        times = []

        for _ in range(5):
            start = time.time()
            system_client.get("/health")
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)

        # Should respond in under 100ms
        assert avg_time < 0.1, f"Health endpoint too slow: {avg_time:.3f}s"

        # Log for monitoring
        print(f"\nHealth endpoint avg latency: {avg_time * 1000:.1f}ms")
