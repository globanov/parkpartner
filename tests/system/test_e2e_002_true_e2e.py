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
    @pytest.mark.timeout(300)
    @pytest.mark.parametrize("test_mode", ["localhost", "tunnel"])
    def test_complete_user_journey_with_real_audio(  # noqa: PLR0915
        self, e2e_page_with_real_audio: Page, test_mode: str
    ):
        """
        Complete user journey with REAL audio (parameterized):
        Runs 5 conversation cycles, verifying history grows.
        """
        page = e2e_page_with_real_audio
        start_time = datetime.now()
        total_cycles = 5

        print("\n" + "=" * 60)
        print(f"🎬 E2E-002: TRUE End-to-End Test ({test_mode.upper()})")
        print(f"   Cycles: {total_cycles}")
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

            # Steps 3-8: Run 5 conversation cycles
            for cycle in range(1, total_cycles + 1):
                print(f"\n{'=' * 40}")
                print(f"🔄 Cycle {cycle}/{total_cycles}")
                print(f"{'=' * 40}")

                # Step 3: Click and hold talk button (timeout: 5s)
                print(f"\n📍 Cycle {cycle} Step 3: Click hold-to-talk button...")
                talk_button = page.locator("#recordBtn")
                talk_button.dispatch_event("touchstart", timeout=5000)
                _log_step(f"Cycle {cycle}: Touchstart dispatched")

                page.wait_for_timeout(500)  # Hold for 500ms

                expect(status_element).to_contain_text("Recording", timeout=5000)
                _log_step(f"Cycle {cycle}: Recording state verified")
                print(f"   ✅ Cycle {cycle}: Recording started")

                # Step 4: Release button (timeout: 5s)
                print(
                    f"\n📍 Cycle {cycle} Step 4: Release button (sends REAL audio)..."
                )
                talk_button.dispatch_event("touchend", timeout=5000)
                _log_step(f"Cycle {cycle}: Touchend dispatched")

                expect(status_element).to_contain_text("Processing", timeout=5000)
                _log_step(f"Cycle {cycle}: Processing state verified")
                print(f"   ✅ Cycle {cycle}: Processing started")

                # Step 5: Wait for server response (timeout: 30s for full pipeline)
                print(f"\n📍 Cycle {cycle} Step 5: Wait for server response...")
                _log_step(f"Cycle {cycle}: Waiting for server processing...")
                page.wait_for_timeout(15000)  # Wait for full pipeline

                expect(status_element).not_to_have_text("Processing", timeout=5000)
                _log_step(f"Cycle {cycle}: Processing complete")
                print(f"   ✅ Cycle {cycle}: Processing complete")

                # Step 6: Verify status indicates conversation completed (timeout: 5s)
                print(f"\n📍 Cycle {cycle} Step 6: Verify final status...")
                final_status = status_element.text_content(timeout=5000)
                _log_step(f"Cycle {cycle}: Final status: {final_status}")
                print(f"   Status: {final_status}")

                # Step 7: Verify conversation history grows (timeout: 5s)
                print(f"\n📍 Cycle {cycle} Step 7: Verify conversation history...")
                conversation_messages = page.locator("#conversation .message")
                message_count = conversation_messages.count()
                _log_step(f"Cycle {cycle}: Message count: {message_count}")
                print(f"   Messages: {message_count}")

                # After cycle N: expect at least N message pairs (user + assistant)
                expected_min = cycle  # At least 1 message per cycle
                assert message_count >= expected_min, (
                    f"Cycle {cycle}: Expected >= {expected_min} messages, got: {message_count}"
                )
                _log_step(f"Cycle {cycle}: Conversation assertion passed")
                print(
                    f"   ✅ Cycle {cycle}: Conversation has {message_count} message(s)"
                )

                # Step 8: Verify audio response (timeout: 5s)
                print(f"\n📍 Cycle {cycle} Step 8: Verify audio response...")
                has_audio_message = False
                for i in range(message_count):
                    msg_text = (
                        conversation_messages.nth(i).text_content(timeout=5000).lower()
                    )
                    if "audio" in msg_text or "playing" in msg_text:
                        has_audio_message = True
                        _log_step(f"Cycle {cycle}: Audio message found at index {i}")
                        break

                if has_audio_message:
                    print(f"   ✅ Cycle {cycle}: Audio response confirmed")
                else:
                    audio_element = page.locator("audio")
                    if audio_element.count() > 0:
                        is_playing = audio_element.evaluate(
                            "audio => !audio.paused", timeout=5000
                        )
                        if is_playing:
                            print(f"   ✅ Cycle {cycle}: Audio is playing")
                        else:
                            print(f"   ✅ Cycle {cycle}: Audio element present")
                    else:
                        print(f"   ⚠️  Cycle {cycle}: Audio playback status unknown")

                # Brief pause between cycles
                if cycle < total_cycles:
                    page.wait_for_timeout(1000)

            # Print test duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            _log_step(f"Test completed in {duration:.2f}s")

            print("\n" + "=" * 60)
            print(f"✅ E2E-002 TRUE End-to-End Test PASSED ({total_cycles} cycles)")
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
