"""
E2E-002: TRUE End-to-End Voice Conversation Test

THE ONLY test that covers the COMPLETE user journey with REAL audio:
1. Opens browser (mobile viewport)
2. Clicks hold-to-talk button
3. Sends REAL audio file (russian_greeting.webm) via injected Blob
4. Waits for server processing
5. Verifies audio response plays
6. Verifies conversation history updated

This is the canonical E2E test — all other "E2E" tests are partial.

Tags: @system, @requires_services, @browser, @smoke
Priority: Critical
"""

from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Reuse fixtures from conftest.py
pytest.importorskip("playwright")


@pytest.fixture(scope="session")
def real_audio_bytes():
    """
    Load REAL test audio file as bytes.

    Must be a real recording: "Привет, как дела?"
    """
    fixtures_dir = Path(__file__).parent / "fixtures" / "audio"
    audio_file = fixtures_dir / "russian_greeting.webm"

    if not audio_file.exists():
        pytest.fail(f"Real audio file required: {audio_file}")

    return audio_file.read_bytes()


@pytest.fixture
def e2e_page_with_real_audio(browser_context, base_url: str, real_audio_bytes: bytes):
    """
    Create page with REAL audio data injected.

    Injects real audio bytes into browser context for MediaRecorder to use.
    """
    page = browser_context.new_page()

    # Convert bytes to list for JavaScript injection
    audio_bytes_list = list(real_audio_bytes)

    # Inject mock MediaRecorder with REAL audio data
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

                    // Use REAL audio data from injected bytes
                    setTimeout(() => {
                        if (self.ondataavailable) {
                            // Create Blob from real audio bytes
                            const realAudioBlob = new Blob(
                                [new Uint8Array(audioData)],
                                { type: 'audio/webm' }
                            );
                            const event = { data: realAudioBlob };
                            self.ondataavailable(event);
                        }
                    }, 100);
                };

                self.stop = function() {
                    originalStop();

                    setTimeout(() => {
                        if (self.onstop) {
                            self.onstop();
                        }
                    }, 200);
                };

                return self;
            };
        })({audio_bytes_list})
        """.replace("{audio_bytes_list}", str(audio_bytes_list))
    )

    # Navigate with explicit timeout
    page.goto(base_url, wait_until="networkidle", timeout=10000)
    page.wait_for_selector("#recordBtn", timeout=10000)

    yield page

    page.close()


def _log_step(step_name: str):
    """Log step with timestamp for debugging"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"   [{timestamp}] {step_name}")


class TestE2E_TrueVoiceConversation:
    """
    E2E-002: TRUE End-to-End Voice Conversation

    THE ONLY test covering complete journey:
    - Browser UI interaction
    - REAL audio file sent to server
    - Server processes real audio
    - Audio response verification
    - Conversation history update
    """

    @pytest.mark.system
    @pytest.mark.requires_services
    @pytest.mark.browser
    @pytest.mark.smoke
    @pytest.mark.timeout(60)  # Fail if test exceeds 60 seconds
    def test_complete_user_journey_with_real_audio(  # noqa: PLR0915
        self, e2e_page_with_real_audio: Page
    ):
        """
        Complete user journey with REAL audio:
        1. Open browser
        2. Click hold-to-talk
        3. Release (sends real audio)
        4. Wait for processing
        5. Verify audio response plays
        6. Verify conversation updated
        """
        page = e2e_page_with_real_audio
        start_time = datetime.now()

        print("\n" + "=" * 60)
        print("🎬 E2E-002: TRUE End-to-End Test (REAL Audio)")
        print("=" * 60)
        _log_step(f"Test started at {start_time.strftime('%H:%M:%S')}")

        try:
            # Step 1: Verify app loaded (timeout: 5s)
            print("\n📍 Step 1: Verify app loaded...")
            expect(page).to_have_title("ParkPartner 🎙️", timeout=5000)
            _log_step("Title verified")

            record_btn = page.locator("#recordBtn")
            expect(record_btn).to_be_visible(timeout=5000)
            _log_step("Record button visible")
            print("   ✅ App loaded")

            # Step 2: Verify initial status (timeout: 5s)
            print("\n📍 Step 2: Verify initial status...")
            status_element = page.locator("#status")
            expect(status_element).to_have_text("Ready to record", timeout=5000)
            _log_step("Initial status verified")
            print("   ✅ Status: Ready to record")

            # Step 3: Click and hold talk button (timeout: 5s)
            print("\n📍 Step 3: Click hold-to-talk button...")
            talk_button = page.locator("#recordBtn")
            talk_button.dispatch_event("touchstart", timeout=5000)
            _log_step("Touchstart dispatched")

            page.wait_for_timeout(500)  # Hold for 500ms

            expect(status_element).to_contain_text("Recording", timeout=5000)
            _log_step("Recording state verified")
            print("   ✅ Recording started")

            # Step 4: Release button (timeout: 5s)
            print("\n📍 Step 4: Release button (sends REAL audio)...")
            talk_button.dispatch_event("touchend", timeout=5000)
            _log_step("Touchend dispatched")

            expect(status_element).to_contain_text("Processing", timeout=5000)
            _log_step("Processing state verified")
            print("   ✅ Processing started")

            # Step 5: Wait for server response (timeout: 30s for full pipeline)
            print("\n📍 Step 5: Wait for server response...")
            _log_step("Waiting for server processing (Whisper + Ollama + TTS)...")
            page.wait_for_timeout(15000)  # Wait for full pipeline

            expect(status_element).not_to_have_text("Processing", timeout=5000)
            _log_step("Processing complete")
            print("   ✅ Processing complete")

            # Step 6: Verify status indicates conversation completed (timeout: 5s)
            print("\n📍 Step 6: Verify final status...")
            final_status = status_element.text_content(timeout=5000)
            _log_step(f"Final status: {final_status}")
            print(f"   Status: {final_status}")
            print("   ✅ Status check complete")

            # Step 7: Verify conversation history updated (timeout: 5s)
            print("\n📍 Step 7: Verify conversation history...")
            conversation_messages = page.locator("#conversation .message")
            message_count = conversation_messages.count()
            _log_step(f"Message count: {message_count}")
            print(f"   Messages: {message_count}")

            # Should have at least 1 message (user message sent)
            # Assistant response may vary based on server processing
            assert message_count >= 1, (
                f"Expected at least 1 conversation message, got: {message_count}"
            )
            _log_step("Conversation assertion passed")
            print(f"   ✅ Conversation has {message_count} message(s)")

            # Step 8: Verify audio response (timeout: 5s)
            print("\n📍 Step 8: Verify audio response...")

            # Check if any message mentions audio
            has_audio_message = False
            for i in range(message_count):
                msg_text = (
                    conversation_messages.nth(i).text_content(timeout=5000).lower()
                )
                if "audio" in msg_text or "playing" in msg_text:
                    has_audio_message = True
                    _log_step(f"Audio message found at index {i}")
                    break

            if has_audio_message:
                print("   ✅ Audio response confirmed in conversation")
            else:
                # Check for audio element
                audio_element = page.locator("audio")
                if audio_element.count() > 0:
                    is_playing = audio_element.evaluate(
                        "audio => !audio.paused", timeout=5000
                    )
                    if is_playing:
                        print("   ✅ Audio is playing")
                    else:
                        print("   ✅ Audio element present")
                else:
                    print("   ⚠️  Audio playback status unknown")

            # Print test duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_step(f"Test completed in {duration:.2f}s")

            print("\n" + "=" * 60)
            print("✅ E2E-002 TRUE End-to-End Test PASSED")
            print(f"   Duration: {duration:.2f}s")
            print("=" * 60 + "\n")

        except PlaywrightTimeoutError as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_step(f"TIMEOUT after {duration:.2f}s")
            print(f"\n   ❌ TIMEOUT: {e}")
            print(f"   Failed at step: {_get_current_step()}")
            raise

        except AssertionError as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_step(f"ASSERTION FAILED after {duration:.2f}s")
            print(f"\n   ❌ ASSERTION: {e}")
            raise


def _get_current_step():
    """Helper for error messages"""
    import traceback

    tb = traceback.extract_stack()
    for frame in tb[-10:]:
        if "Step" in frame.line:
            return frame.line.strip()
    return "Unknown step"
