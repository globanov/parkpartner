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

## E2E Scenarios Summary

| ID | Scenario | Priority | Status | Test File |
|----|----------|----------|--------|-----------|
| E2E-001 | Complete Voice Conversation | 🔴 Critical | ✅ Implemented | `test_e2e_002_true_e2e.py` |
| E2E-002 | Empty Audio File Handling | 🟡 High | ✅ Implemented | `test_routes.py`, `test_adapters.py` |
| E2E-003 | Corrupted WebM File (iOS Bug) | 🔴 Critical | ✅ Implemented | `test_routes.py`, `test_adapters.py` |
| E2E-004 | Invalid Auth Token | 🟡 High | ❌ Not Started | — |
| E2E-005 | Session History Truncation | 🟡 High | ✅ Implemented | `test_service.py` |
| E2E-006 | Ollama Timeout Handling | 🟡 High | ❌ Not Started | — |
| E2E-007 | Multiple Audio Formats | 🟢 Medium | ✅ Implemented | `test_routes.py` |
| E2E-008 | iOS Safari Real Device | 🔴 Critical | ❌ Not Started | — |
| E2E-009 | Long Session Memory Leak | 🟡 High | ❌ Not Started | — |

---

## E2E Scenarios Detail

### E2E-001: Complete Voice Conversation ✅

**Priority:** 🔴 Critical | **Status:** ✅ Implemented (2026-03-29)

**Test file:** `tests/system/test_e2e_002_true_e2e.py`

**What it tests:**
1. Open browser (mobile viewport)
2. Click hold-to-talk button
3. Send audio (mocked MediaRecorder)
4. Server processes request
5. Verify status changed from "Ready to record"
6. Verify full pipeline executed

**Run:**
```bash
pytest tests/system/test_e2e_002_true_e2e.py -v -s
python run_e2e_tests.py -v  # Includes all E2E tests
```

**Note:** This is THE ONLY true E2E test covering browser + server in one test.

---

### E2E-002: Empty Audio File Handling ✅

**Priority:** 🟡 High | **Status:** ✅ Implemented

**Test files:**
- `tests/test_routes.py::TestValidationUtilities::test_validate_audio_file_too_large`
- `tests/test_adapters.py::TestWhisperAdapterAdditional::test_transcribe_audio_whitespace_only`

**What it tests:** Empty or minimal audio files rejected with 400 error.

---

### E2E-003: Corrupted WebM File (iOS Bug) ✅

**Priority:** 🔴 Critical | **Status:** ✅ Implemented

**Test files:**
- `tests/test_routes.py::TestProcessAdditional::test_process_empty_file`
- `tests/test_adapters.py` - Various invalid audio tests

**What it tests:** Corrupted/minimal WebM files (iOS Safari bug ~110 bytes) rejected with 400.

---

### E2E-004: Invalid Auth Token ❌

**Priority:** 🟡 High | **Status:** ❌ Not Started

**What to test:** Invalid auth tokens rejected with 401/403.

---

### E2E-005: Session History Truncation ✅

**Priority:** 🟡 High | **Status:** ✅ Implemented

**Test files:**
- `tests/test_service.py::TestProcessConversation::test_session_history_limited`
- `tests/test_service.py::TestProcessConversation::test_session_history_updated`

**What it tests:** Session history limited to max 6 messages (FIFO).

---

### E2E-006: Ollama Timeout Handling ❌

**Priority:** 🟡 High | **Status:** ❌ Not Started

**What to test:** Ollama timeouts handled gracefully (504 error).

---

### E2E-007: Multiple Audio Formats ✅

**Priority:** 🟢 Medium | **Status:** ✅ Implemented

**Test files:**
- `tests/test_routes.py::TestValidationUtilities::test_validate_audio_valid_types[...]`
- Tests for: `audio/webm`, `audio/wav`, `audio/mp4`, `audio/mpeg`

**What it tests:** WebM, WAV, MP4, MP3 accepted. Invalid formats rejected with 400.

---

### E2E-008: iOS Safari Real Device ❌

**Priority:** 🔴 Critical | **Status:** ❌ Not Started

**What to test:** Hold-to-talk works on real iOS Safari with touch events.

---

### E2E-009: Long Session Memory Leak ❌

**Priority:** 🟡 High | **Status:** ❌ Not Started

**What to test:** No memory leaks during extended session (50+ requests).

**Note:** `run_e2e_stress.py` exists but is not integrated into E2E suite.

---

## Test Coverage Analysis

### True E2E Tests (Browser + Server)

| Test | Coverage |
|------|----------|
| `test_e2e_002_true_e2e.py::test_complete_user_journey_with_mocked_audio` | ✅ Full pipeline |

### Partial E2E Tests (Browser OR Server)

| Test | Coverage | Gap |
|------|----------|-----|
| `test_e2e_001_browser.py::test_complete_user_journey` | Browser UI only | ❌ No real audio |
| `test_e2e_001_voice_conversation.py::test_complete_flow_end_to_end` | API only | ❌ No browser UI |

### Redundant Tests (Candidates for Removal)

| Duplicate Group | Tests | Recommendation |
|-----------------|-------|----------------|
| Health checks | `test_server_available`, `test_server_starts_successfully`, `test_health_endpoint_responds`, `test_health_endpoint` (×4) | Keep 1, remove 3 |
| Frontend checks | `test_frontend_loads_correctly`, `test_frontend_serves_html`, `test_frontend_endpoint` (×3) | Keep 1, remove 2 |
| Audio validation | `test_audio_validation_rejects_invalid_format`, `test_unsupported_audio_format` (×2) | Keep 1 |
| File size validation | `test_audio_validation_rejects_oversized_file`, `test_file_too_large` (×2) | Keep 1 |

**Total redundant tests: ~8**

---

## Tech Debt

### 1. Redundant Tests to Remove

Remove duplicate tests to reduce maintenance burden:

```bash
# Candidates for removal (after verification):
- tests/system/test_full_flow.py::TestFullApplicationFlow::test_health_endpoint_responds
- tests/system/test_full_flow.py::TestFullApplicationFlow::test_frontend_serves_html
- tests/integration/test_full_pipeline.py::TestHealthAndFrontend::*
```

### 2. Move to Integration Tests

Tests that don't require browser should be in `tests/integration/`:

- `tests/system/test_e2e_001_voice_conversation.py` → Rename to `test_api_voice_conversation.py`
- `tests/system/test_full_flow.py` → Merge with `tests/integration/test_full_pipeline.py`

### 3. Browser-Only Tests

Keep in `tests/system/` (require Playwright):

- `tests/system/test_e2e_001_browser.py` — UI interaction tests
- `tests/system/test_e2e_002_true_e2e.py` — Full E2E test

---

## Prerequisites

See [README.md](../README.md#prerequisites) for Ollama, FFmpeg, Python setup.

Requires Playwright:
```bash
pip install playwright && playwright install chromium
```

---

## Running Tests

### All E2E Tests
```bash
python run_e2e_tests.py -v
```

### Specific Test
```bash
# True E2E test (browser + server)
pytest tests/system/test_e2e_002_true_e2e.py -v -s

# Browser UI tests only
pytest tests/system/test_e2e_001_browser.py -v -s

# API tests only
pytest tests/system/test_e2e_001_voice_conversation.py -v -s
```

### Show Browser (Debug)
```bash
pytest tests/system/test_e2e_002_true_e2e.py -v -s --headed
```
