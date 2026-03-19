# ParkPartner E2E Tests

## Quick Start

```bash
python run_e2e_tests.py -v  # Recommended - auto server management
./run_e2e_tests.sh -v       # macOS/Linux only
```

## Scripts

| Script | Purpose |
|--------|---------|
| `python parkpartner.py` | Start server (http://localhost:8000) |
| `./start_parkpartner_with_tunnel.sh` | Server + HTTPS tunnel |
| `python run_e2e_tests.py` | E2E tests with auto server management |

---

## E2E Scenarios

### E2E-001: Complete Voice Conversation ✅

**Priority:** 🔴 Critical | **Status:** ✅ Done

Verify user journey: voice input → audio response via browser automation.

**Test files:**
- `tests/system/test_e2e_001_browser.py` - Browser-based
- `tests/system/test_e2e_001_voice_conversation.py` - API-based

**Steps:**
1. Open browser (mobile viewport)
2. Click hold-to-talk button
3. Hold 1 second, release
4. Wait for response (<10 seconds)
5. Verify audio plays

**Expected:**
- ✅ Button provides visual feedback
- ✅ Processing indicator shows
- ✅ Audio response plays automatically
- ✅ Total time <15 seconds

**Run:**
```bash
pytest tests/system/test_e2e_001_browser.py -v -s
pytest tests/system/test_e2e_001_browser.py -v -s --headed  # Show browser
```

---

### E2E-002: Empty Audio File Handling 🟡

**Priority:** 🟡 High | **Status:** 🟡 In Progress

Verify empty audio files (0 bytes) rejected with 400 error.

---

### E2E-003: Corrupted WebM File (iOS Bug) ✅

**Priority:** 🔴 Critical | **Status:** ✅ Done

Verify corrupted WebM files (110 bytes, iOS Safari bug) rejected with 400.

---

### E2E-004: Invalid Auth Token 🟢

**Priority:** 🟡 High | **Status:** 🟢 Not Started

Verify invalid auth tokens rejected with 401/403.

---

### E2E-005: Session History Truncation ✅

**Priority:** 🟡 High | **Status:** ✅ Done

Verify session history limited to max 6 messages (FIFO).

---

### E2E-006: Ollama Timeout Handling 🟢

**Priority:** 🟡 High | **Status:** 🟢 Not Started

Verify Ollama timeouts handled gracefully (504 error).

---

### E2E-007: Multiple Audio Formats ✅

**Priority:** 🟢 Medium | **Status:** ✅ Done

Verify WebM, WAV, MP4, MP3 accepted. Invalid formats rejected with 400.

---

### E2E-008: iOS Safari Real Device 🟢

**Priority:** 🔴 Critical | **Status:** 🟢 Not Started

Verify hold-to-talk works on real iOS Safari with touch events.

---

### E2E-009: Long Session Memory Leak 🟢

**Priority:** 🟡 High | **Status:** 🟢 Not Started

Verify no memory leaks during extended session (50+ requests).

---

## Prerequisites

See [README.md](../README.md#prerequisites) for Ollama, FFmpeg, Python setup.

Requires Playwright:
```bash
pip install playwright && playwright install chromium
```

## Troubleshooting

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
pkill -f "uvicorn.*parkpartner"
```

**Server failed to start:**
```bash
tail -50 logs/e2e_test_*.log
```

**Playwright not installed:**
```bash
pip install playwright && playwright install chromium
```

**Browser test failures:**
```bash
python run_e2e_tests.py --headed  # Show browser
```

---

**Status:** ✅ Ready | **Scripts:** `run_e2e_tests.py`, `run_e2e_tests.sh`
