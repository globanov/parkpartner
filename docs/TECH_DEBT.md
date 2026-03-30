# ParkPartner Test Tech Debt — Migration Plan

**Created:** 2026-03-29  
**Priority:** Medium  
**Estimated Effort:** ~3 hours

---

## Overview

Current test structure mislabels many tests as "E2E" or "system" when they are actually:
- **UI tests** (browser-only, no server interaction)
- **Integration tests** (API-only, no browser)
- **Redundant tests** (duplicates of existing tests)

**True E2E tests** (browser + server in one test): 1  
**Mislabelled tests:** ~23  
**Redundant tests:** ~8

---

## 1. Tests to Move: system/ → integration/

### 1.1 test_e2e_001_browser.py — UI-Only Tests

| Test Name | Current Location | Target Location | Reason | Priority |
|-----------|------------------|-----------------|--------|----------|
| `test_no_console_errors` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | Browser-only, no server verification | Low |
| `test_media_devices_available` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | Browser API check, no server | Low |
| `test_app_loads_in_browser` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | Static page load, no interaction | Low |
| `test_hold_to_talk_button_interaction` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | UI interaction only, no audio sent | Low |
| `test_audio_recording_indicator` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | UI state change only | Low |
| `test_processing_state_after_release` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | UI state change only | Low |
| `test_audio_response_playback` | `tests/system/test_e2e_001_browser.py` | `tests/integration/test_browser_ui.py` | Audio element check, no real playback | Low |

**Keep in system/:**
- `test_complete_user_journey` — E2E test (browser + server status change)
- `test_server_available` — Health check for E2E suite

**Reason:** These tests verify UI behavior only. They don't verify server processing, audio response, or conversation history.

---

### 1.2 test_e2e_001_voice_conversation.py — API-Only Tests

| Test Name | Current Location | Target Location | Reason | Priority |
|-----------|------------------|-----------------|--------|----------|
| `test_server_starts_successfully` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | API health check, no browser | Medium |
| `test_frontend_loads_correctly` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | HTTP GET, no browser | Medium |
| `test_send_voice_message` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | API call, no browser | Medium |
| `test_verify_response_audio` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | Response validation, no browser | Medium |
| `test_verify_conversation_history` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | Stub (no state access) | Low |
| `test_complete_flow_end_to_end` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_api_endpoints.py` | API flow, no browser | Medium |
| `test_response_time_sla` | `tests/system/test_e2e_001_voice_conversation.py` | `tests/integration/test_performance.py` | Performance test | Low |

**Reason:** These tests use `requests` library, not browser. They verify API behavior, not user experience.

---

### 1.3 test_full_flow.py — Mostly Integration Tests

| Test Name | Current Location | Target Location | Reason | Priority |
|-----------|------------------|-----------------|--------|----------|
| `test_health_endpoint_responds` | `tests/system/test_full_flow.py` | `tests/integration/test_api_endpoints.py` | Duplicate health check | High (remove) |
| `test_frontend_serves_html` | `tests/system/test_full_flow.py` | `tests/integration/test_api_endpoints.py` | Duplicate frontend check | High (remove) |
| `test_audio_validation_rejects_invalid_format` | `tests/system/test_full_flow.py` | `tests/integration/test_validation.py` | Validation test | Medium |
| `test_audio_validation_rejects_oversized_file` | `tests/system/test_full_flow.py` | `tests/integration/test_validation.py` | Validation test | Medium |
| `test_full_conversation_with_real_services` | `tests/system/test_full_flow.py` | `tests/integration/test_api_endpoints.py` | Skipped (requires services) | Low |
| `test_session_state_is_maintained` | `tests/system/test_full_flow.py` | `tests/integration/test_state.py` | State test (stub) | Low |
| `test_multiple_sessions_are_isolated` | `tests/system/test_full_flow.py` | `tests/integration/test_state.py` | State isolation test | Medium |
| `test_app_recovers_from_invalid_request` | `tests/system/test_full_flow.py` | `tests/integration/test_error_handling.py` | Error recovery test | Medium |
| `test_concurrent_requests_dont_corrupt_state` | `tests/system/test_full_flow.py` | `tests/integration/test_concurrency.py` | Concurrency test | Medium |
| `test_health_endpoint_latency` | `tests/system/test_full_flow.py` | `tests/integration/test_performance.py` | Performance test | Low |

**Reason:** These are integration tests (TestClient, no browser). Many are duplicates of existing tests.

---

## 2. Redundant Tests to Remove

### 2.1 Health Check Duplicates (Keep 1, Remove 3)

| Test | Location | Keep/Remove | Reason |
|------|----------|-------------|--------|
| `test_server_available` | `test_e2e_001_browser.py` | ✅ Keep | Used by E2E suite |
| `test_server_starts_successfully` | `test_e2e_001_voice_conversation.py` | ❌ Remove | Duplicate |
| `test_health_endpoint_responds` | `test_full_flow.py` | ❌ Remove | Duplicate |
| `test_health_endpoint` | `test_full_pipeline.py` | ❌ Remove | Duplicate |

**Effort:** 30 min

---

### 2.2 Frontend Check Duplicates (Keep 1, Remove 2)

| Test | Location | Keep/Remove | Reason |
|------|----------|-------------|--------|
| `test_frontend_loads_correctly` | `test_e2e_001_voice_conversation.py` | ✅ Keep | Detailed checks |
| `test_frontend_serves_html` | `test_full_flow.py` | ❌ Remove | Duplicate |
| `test_frontend_endpoint` | `test_full_pipeline.py` | ❌ Remove | Duplicate |

**Effort:** 20 min

---

### 2.3 Validation Test Duplicates (Keep 1, Remove 2)

| Test | Location | Keep/Remove | Reason |
|------|----------|-------------|--------|
| `test_audio_validation_rejects_invalid_format` | `test_full_flow.py` | ✅ Keep | Clear name |
| `test_unsupported_audio_format` | `test_full_pipeline.py` | ❌ Remove | Duplicate |
| `test_audio_validation_rejects_oversized_file` | `test_full_flow.py` | ✅ Keep | Clear name |
| `test_file_too_large` | `test_full_pipeline.py` | ❌ Remove | Duplicate |

**Effort:** 20 min

---

### 2.4 Summary: Redundant Tests

| Category | Keep | Remove | Effort |
|----------|------|--------|--------|
| Health checks | 1 | 3 | 30 min |
| Frontend checks | 1 | 2 | 20 min |
| Validation tests | 2 | 2 | 20 min |
| **Total** | **4** | **7** | **~1 hour** |

---

## 3. Migration Steps

### Phase 1: Create New Integration Test Files (30 min)

```bash
# Create new files
touch tests/integration/test_browser_ui.py
touch tests/integration/test_api_endpoints.py
touch tests/integration/test_validation.py
touch tests/integration/test_state.py
touch tests/integration/test_error_handling.py
touch tests/integration/test_concurrency.py
touch tests/integration/test_performance.py
```

### Phase 2: Move Tests (1 hour)

1. Move browser UI tests → `test_browser_ui.py`
2. Move API tests → `test_api_endpoints.py`
3. Move validation tests → `test_validation.py`
4. Move state tests → `test_state.py`
5. Move error handling → `test_error_handling.py`
6. Move concurrency → `test_concurrency.py`
7. Move performance → `test_performance.py`

### Phase 3: Remove Duplicates (30 min)

1. Delete redundant health checks
2. Delete redundant frontend checks
3. Delete redundant validation tests
4. Update imports/references

### Phase 4: Update Documentation (30 min)

1. Update `docs/E2E.md` with new structure
2. Update `docs/TESTING.md` with test categories
3. Update `README.md` test commands
4. Update `E2E_TEST_SCENARIOS.md` (if keeping)

### Phase 5: Verify (30 min)

```bash
# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/integration/ -v

# Run system tests (E2E only)
pytest tests/system/ -v

# Run E2E test runner
python run_e2e_tests.py -v
```

---

## 4. Timeline Estimate

| Phase | Task | Estimated Time |
|-------|------|----------------|
| 1 | Create new files | 30 min |
| 2 | Move tests | 1 hour |
| 3 | Remove duplicates | 30 min |
| 4 | Update docs | 30 min |
| 5 | Verify | 30 min |
| **Total** | | **~3 hours** |

---

## 5. Post-Migration Structure

```
tests/
├── unit/                  # Unit tests (mocked)
│   ├── test_adapters.py
│   ├── test_service.py
│   ├── test_config.py
│   └── test_routes.py
│
├── integration/           # Integration tests (real services, no browser)
│   ├── test_browser_ui.py        (moved from system/)
│   ├── test_api_endpoints.py     (moved from system/)
│   ├── test_validation.py        (merged)
│   ├── test_state.py             (moved from system/)
│   ├── test_error_handling.py    (moved from system/)
│   ├── test_concurrency.py       (moved from system/)
│   └── test_performance.py       (moved from system/)
│
└── system/                # TRUE E2E tests (browser + server)
    ├── test_e2e_002_true_e2e.py  (THE ONLY true E2E test)
    └── conftest.py               (shared fixtures)
```

---

## 6. Benefits

| Benefit | Impact |
|---------|--------|
| Clear test categorization | Easy to find tests |
| Reduced redundancy | Less maintenance |
| Faster test runs | Only run what you need |
| Accurate naming | "E2E" means browser + server |
| Better CI/CD | Run integration vs E2E separately |

---

## 7. Risks

| Risk | Mitigation |
|------|------------|
| Broken imports | Update all imports before committing |
| Lost test coverage | Run full suite before/after, compare counts |
| CI/CD pipeline breaks | Update pipeline config in same PR |

---

## 8. Timeout Audit — All Tests

**Priority:** High (prevents hangs)  
**Estimate:** 2 hours  
**Status:** ✅ Started (test_e2e_002_true_e2e.py complete)

### Task

Audit ALL test files for missing timeouts.

### Files to Check

| Directory | File Count | Test Count |
|-----------|------------|------------|
| `tests/system/` | 4 files | 19 tests |
| `tests/integration/` | 1 file | 4 tests |
| `tests/` (root) | 4 files | ~50 tests |
| **Total** | **9 files** | **~73 tests** |

### Checklist for Each Test

- [ ] Playwright operations have explicit `timeout` parameter
- [ ] HTTP requests have `timeout` parameter
- [ ] `@pytest.mark.timeout()` decorator is set
- [ ] `asyncio.wait_for()` has timeout

### Completed

| File | Timeout Decorator | Playwright Timeouts | HTTP Timeouts | Status |
|------|-------------------|---------------------|---------------|--------|
| `test_e2e_002_true_e2e.py` | ✅ `@pytest.mark.timeout(60)` | ✅ All operations | N/A | ✅ Done |

### Pending

| File | Priority | Estimated Time |
|------|----------|----------------|
| `tests/system/test_e2e_001_browser.py` | High | 30 min |
| `tests/system/test_e2e_001_voice_conversation.py` | High | 30 min |
| `tests/system/test_full_flow.py` | Medium | 20 min |
| `tests/integration/test_full_pipeline.py` | Medium | 20 min |
| `tests/test_routes.py` | Low | 20 min |
| `tests/test_adapters.py` | Low | 20 min |
| **Total** | | **~2 hours** |

### Timeout Standards

| Operation | Timeout Value |
|-----------|---------------|
| Page load (`page.goto()`) | 10 seconds |
| Element visible (`wait_for_selector()`) | 5 seconds |
| Assertion (`expect().to_*`) | 5 seconds |
| Full pipeline (Whisper + Ollama + TTS) | 30 seconds |
| Test total (`@pytest.mark.timeout`) | 60 seconds |
| HTTP requests (`requests.post()`) | 60 seconds |

### Example Pattern

```python
@pytest.mark.timeout(60)  # Fail if test exceeds 60 seconds
def test_something(page: Page):
    # Page load with timeout
    page.goto(base_url, timeout=10000)
    
    # Element wait with timeout
    page.wait_for_selector("#btn", timeout=5000)
    
    # Assertion with timeout
    expect(element).to_be_visible(timeout=5000)
    
    # Full pipeline wait
    page.wait_for_timeout(15000)  # Whisper + Ollama + TTS
```

---

## Future: Simplify docs/E2E.md

**Priority:** Low  
**Status:** TODO

- **Current:** Large, detailed coverage matrix with all scenarios
- **Action:** Trim to essential scenarios only (E2E-001, E2E-002, E2E-003)
- **When:** After test migration complete (tests moved to integration/)

---

=== END OF FILE ===
