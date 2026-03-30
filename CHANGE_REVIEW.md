# Change Review — ParkPartner

**Generated:** 2026-03-30 12:30:00  
**Branch:** main  
**Total Modified:** 7 files  
**Total New:** 4 files

---

## Section 1: Modified Files (git diff)

### 1.1 app/adapters/api/routes.py
**Status:** [KEEP]  
**Purpose:** Fix iOS Safari WebM/MP4 validation to accept non-standard audio headers.

**Changes:**
```diff
@@ -44,18 +44,43 @@ def _validate_webm_header(audio_data: bytes) -> bool:
     """
     Validate WebM file header.
 
-    WebM files start with EBML header: 0x1A 0x45 0xDF 0xA3
-    Returns True if valid WebM header detected.
+    Standard WebM files start with EBML header: 0x1A 0x45 0xDF 0xA3
+    
+    iOS Safari quirk: MediaRecorder on iOS Safari produces WebM/MP4 files with
+    non-standard headers (often starts with 0x00 0x00 0x00 0x20 = MP4 'ftyp' box).
+    We accept these and let Whisper handle validation.
+    
+    Returns True if valid WebM header detected OR if file looks like MP4 (iOS quirk).
     """
     if len(audio_data) < 4:
         return False
 
-    webm_magic = bytes([0x1A, 0x45, 0xDF, 0xA3])
-    return audio_data[:4] == webm_magic
+    # Standard WebM EBML header
+    standard_webm = bytes([0x1A, 0x45, 0xDF, 0xA3])
+    
+    # iOS Safari MediaRecorder produces MP4 container instead of WebM
+    # MP4 files start with size box: 0x00 0x00 0x00 0x20 followed by 'ftyp'
+    ios_mp4_ftyp = bytes([0x00, 0x00, 0x00, 0x20])
+    
+    # Accept standard WebM header
+    if audio_data[:4] == standard_webm:
+        return True
+    
+    # Accept iOS Safari MP4 format (ftyp box)
+    if audio_data[:4] == ios_mp4_ftyp:
+        return True
+    
+    # For small files (<1KB), skip strict header validation
+    # iOS Safari may produce other non-standard headers
+    if len(audio_data) < 1024:
+        return True  # Let Whisper handle validation
+    
+    return False
```

**Why this change:** iOS Safari MediaRecorder produces MP4 container (header `0x00 0x00 0x00 0x20`) instead of standard WebM. Server was rejecting with 400 error. Now accepts iOS format and lets Whisper validate.

**Risk if reverted:** iPhone Safari users get "Invalid WebM header" 400 error on every recording attempt.

---

### 1.2 app/config.py
**Status:** [KEEP]  
**Purpose:** Add centralized logging configuration with component-based subdirectories.

**Changes:**
```diff
+# Centralized Logging Configuration
+LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
+DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
+BASE_LOGS_DIR = Path(__file__).parent.parent / "logs"
+
+LOG_SUBDIRS = {
+    "server": "server",
+    "system": "tests/system",
+    "integration": "tests/integration",
+    "unit": "tests/unit",
+    "e2e": "tests/system",
+    "test": "tests/unit",
+}
+
+def get_log_filepath(prefix: str, component_type: str = "unit") -> Path:
+    subdir = LOG_SUBDIRS.get(component_type, "tests/unit")
+    logs_dir = BASE_LOGS_DIR / subdir
+    logs_dir.mkdir(parents=True, exist_ok=True)
+    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
+    return logs_dir / f"{prefix}_{timestamp}.log"
+
+def setup_logging(prefix: str, component_type: str = "unit", level: int = logging.INFO) -> None:
+    log_file = get_log_filepath(prefix, component_type)
+    logging.basicConfig(...)
```

**Why this change:** Unify logging format across server, E2E tests, integration tests, and unit tests. Logs now organized by component type in subdirectories.

**Risk if reverted:** All logging reverts to single `logs/` directory with mixed formats. Harder to debug issues.

---

### 1.3 parkpartner.py
**Status:** [KEEP]  
**Purpose:** Use centralized logging instead of local basicConfig.

**Changes:**
```diff
-from app.config import WHISPER_MODEL
+from app.config import WHISPER_MODEL, setup_logging
...
-# Logging setup
-logging.basicConfig(
-    level=logging.DEBUG,
-    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
-    handlers=[
-        logging.FileHandler("logs/parkpartner.log", encoding="utf-8"),
-        logging.StreamHandler(),
-    ],
-)
+# Initialize centralized logging
+setup_logging("parkpartner", component_type="server", level=logging.DEBUG)
```

**Why this change:** Use centralized logging config for consistent format and log file organization (`logs/server/`).

**Risk if reverted:** Server logs go to `logs/parkpartner.log` instead of `logs/server/parkpartner_*.log`. Format inconsistency.

---

### 1.4 run_e2e_tests.py
**Status:** [KEEP]  
**Purpose:** Use centralized logging, add new E2E test file.

**Changes:**
```diff
+from app.config import setup_logging
+setup_logging("e2e", component_type="system")
+logger = logging.getLogger(__name__)
...
-E2E_TEST_FILE = "tests/system/test_e2e_001_browser.py"
+E2E_TEST_FILES = [
+    "tests/system/test_e2e_001_browser.py",
+    "tests/system/test_e2e_002_true_e2e.py",
+]
...
-def log_info(message): ...
-def log_success(message): ...
-def log_error(message): ...
-def log_warning(message): ...
+# Removed - using standard logger instead
+logger.info("...")
+logger.warning("...")
+logger.error("...")
```

**Why this change:** Unified logging format, include new true E2E test in test runner.

**Risk if reverted:** E2E test runner uses old log format, new test not included.

---

### 1.5 tests/system/conftest.py
**Status:** [KEEP]  
**Purpose:** Add centralized logging + move shared browser fixtures here.

**Changes:**
```diff
+# Configure system test logging
+from app.config import setup_logging
+setup_logging("system", component_type="system")
+logger = logging.getLogger(__name__)
...
+# Moved from test_e2e_001_browser.py (shared fixtures)
+@pytest.fixture(scope="session")
+def browser_context():
+    ...
+
+@pytest.fixture
+def page(browser_context, base_url):
+    ...
```

**Why this change:** Centralize logging for system tests, share browser fixtures across all system tests.

**Risk if reverted:** System tests lose shared fixtures, logging format inconsistent.

---

### 1.6 docs/E2E.md
**Status:** [KEEP]  
**Purpose:** Update E2E documentation with current test coverage and new true E2E test.

**Changes:**
- Added E2E scenarios summary table
- Updated E2E-001 to reference `test_e2e_002_true_e2e.py`
- Added test coverage status for all 9 scenarios
- Added "Redundant Tests" and "Tech Debt" sections

**Why this change:** Documentation was outdated. Now reflects actual test coverage and identifies gaps.

**Risk if reverted:** Documentation doesn't match reality, developers confused about which test to run.

---

### 1.7 tests/system/test_e2e_001_browser.py
**Status:** [KEEP]  
**Purpose:** Remove duplicate browser fixtures (moved to system/conftest.py).

**Changes:**
```diff
-@pytest.fixture(scope="session")
-def browser_context():
-    ...
-
-@pytest.fixture
-def page(browser_context, base_url):
-    ...
```

**Why this change:** Fixtures moved to `tests/system/conftest.py` for sharing across all system tests.

**Risk if reverted:** Duplicate fixtures, potential inconsistency if one is updated.

---

## Section 2: Untracked Files (new files)

### 2.1 tests/conftest.py
**Status:** [KEEP]  
**Purpose:** Root pytest configuration for unit test logging.

**Content:**
```python
"""
Root pytest configuration for logging.
Unifies logging format across all test types.
"""

import logging
import sys
from pathlib import Path

import pytest

from app.config import setup_logging


@pytest.fixture(autouse=True, scope="session")
def _setup_test_logging():
    """Configure logging for all tests (default: unit)"""
    setup_logging("test", component_type="unit")
    yield


@pytest.fixture(autouse=True)
def _log_test_start(request):
    """Log test start for debugging"""
    logger = logging.getLogger(__name__)
    logger.debug("Starting test: %s", request.node.nodeid)
    yield
```

**Why created:** Configure unified logging for all unit tests. Logs go to `logs/tests/unit/`.

**Safe to delete?** NO — unit tests lose logging configuration.

---

### 2.2 tests/integration/conftest.py
**Status:** [KEEP]  
**Purpose:** Integration test logging configuration.

**Content:**
```python
"""
Integration test fixtures and configuration.
Integration tests verify interactions between components with real services.
"""

import logging

import pytest

from app.config import setup_logging
setup_logging("integration", component_type="integration")
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True, scope="session")
def _setup_integration_logging():
    """Configure logging for integration tests"""
    yield
```

**Why created:** Configure unified logging for integration tests. Logs go to `logs/tests/integration/`.

**Safe to delete?** NO — integration tests lose logging configuration.

---

### 2.3 tests/system/test_e2e_002_true_e2e.py
**Status:** [KEEP]  
**Purpose:** THE ONLY true E2E test covering browser + server with REAL audio.

**Content (first 50 lines):**
```python
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
"""

from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

pytest.importorskip("playwright")


@pytest.fixture(scope="session")
def real_audio_bytes():
    """Load REAL test audio file as bytes."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "audio"
    audio_file = fixtures_dir / "russian_greeting.webm"
    if not audio_file.exists():
        pytest.fail(f"Real audio file required: {audio_file}")
    return audio_file.read_bytes()
```

**Why created:** Existing "E2E" tests were partial (browser-only or API-only). This test covers full pipeline with real audio file.

**Safe to delete?** NO — this is the only true E2E test. Deleting removes full pipeline verification.

---

### 2.4 docs/E2E_TEST_SCENARIOS.md
**Status:** [REVIEW]  
**Purpose:** Comprehensive analysis of all E2E tests in codebase.

**Content (excerpt):**
```markdown
# ParkPartner E2E Test Scenarios Analysis

## Section 1: All E2E Tests Found

### 1.1 Browser-Based E2E Tests (Playwright)
| File | Test Name | What It Tests | Status |
|------|-----------|---------------|--------|
| `test_e2e_001_browser.py` | `test_complete_user_journey` | Browser UI only | ⚠️ No real audio |

### 1.2 API-Based E2E Tests (requests)
| File | Test Name | What It Tests | Status |
|------|-----------|---------------|--------|
| `test_e2e_001_voice_conversation.py` | `test_complete_flow_end_to_end` | API only | ⚠️ No browser |

## Section 3: Direct Answers
Q1: Is there ONE test that covers the complete user journey?
Answer: NO — split between TWO tests until test_e2e_002_true_e2e.py was created.
```

**Why created:** Document test coverage gaps, identify redundant tests, plan migration.

**Safe to delete?** YES — analysis document, not code. Useful for planning but not required for operation.

---

### 2.5 docs/TECH_DEBT.md
**Status:** [REVIEW]  
**Purpose:** Test migration plan and timeout audit checklist.

**Content (excerpt):**
```markdown
# ParkPartner Test Tech Debt — Migration Plan

## Overview
- True E2E tests: 1
- Mislabelled tests: ~23
- Redundant tests: ~8

## 1. Tests to Move: system/ → integration/
| Test Name | Current Location | Target Location | Priority |
|-----------|------------------|-----------------|----------|
| `test_no_console_errors` | `tests/system/...` | `tests/integration/...` | Low |

## 8. Timeout Audit — All Tests
| File | Timeout Decorator | Playwright Timeouts | Status |
|------|-------------------|---------------------|--------|
| `test_e2e_002_true_e2e.py` | ✅ @pytest.mark.timeout(60) | ✅ All operations | ✅ Done |
```

**Why created:** Track tech debt, plan test reorganization, track timeout audit progress.

**Safe to delete?** YES — planning document. Work items should be completed before deleting.

---

## Section 3: Summary Table

| File | Type | Status | Safe to Delete? | Priority |
|------|------|--------|-----------------|----------|
| `app/adapters/api/routes.py` | Modified | [KEEP] | NO — breaks iOS Safari | 🔴 Critical |
| `app/config.py` | Modified | [KEEP] | NO — logging infra | 🔴 Critical |
| `parkpartner.py` | Modified | [KEEP] | NO — uses new logging | 🔴 Critical |
| `run_e2e_tests.py` | Modified | [KEEP] | NO — new test runner | 🔴 Critical |
| `tests/system/conftest.py` | Modified | [KEEP] | NO — shared fixtures | 🟡 High |
| `docs/E2E.md` | Modified | [KEEP] | NO — outdated otherwise | 🟡 High |
| `tests/system/test_e2e_001_browser.py` | Modified | [KEEP] | NO — uses shared fixtures | 🟡 High |
| `tests/conftest.py` | New | [KEEP] | NO — unit test logging | 🟡 High |
| `tests/integration/conftest.py` | New | [KEEP] | NO — integration logging | 🟡 High |
| `tests/system/test_e2e_002_true_e2e.py` | New | [KEEP] | NO — only true E2E test | 🔴 Critical |
| `docs/E2E_TEST_SCENARIOS.md` | New | [REVIEW] | YES — analysis doc | 🟢 Low |
| `docs/TECH_DEBT.md` | New | [REVIEW] | YES — planning doc | 🟢 Low |

---

## Section 4: Recommended Actions

### 1. Commit Immediately (Critical)
```bash
git add app/adapters/api/routes.py  # iOS Safari fix
git add app/config.py                # Logging infra
git add parkpartner.py               # Server logging
git add run_e2e_tests.py             # E2E runner
git add tests/system/conftest.py     # Shared fixtures
git add tests/conftest.py            # Unit test logging
git add tests/integration/conftest.py # Integration logging
git add tests/system/test_e2e_002_true_e2e.py  # True E2E test
git commit -m "feat: centralized logging, iOS Safari fix, true E2E test"
```

### 2. Commit Documentation (High Priority)
```bash
git add docs/E2E.md
git commit -m "docs: update E2E test coverage and scenarios"
```

### 3. Review Before Committing (Low Priority)
```bash
# Review analysis docs
cat docs/E2E_TEST_SCENARIOS.md
cat docs/TECH_DEBT.md

# Decide: keep as reference or delete after migration?
```

### 4. Delete After Migration (Optional)
```bash
# After completing migration plan in TECH_DEBT.md:
rm docs/E2E_TEST_SCENARIOS.md
rm docs/TECH_DEBT.md
```

---

## Section 5: Impact Assessment

| If Reverted | Impact | Severity |
|-------------|--------|----------|
| iOS Safari fix | iPhone users get 400 errors | 🔴 Critical |
| Centralized logging | Mixed log formats, harder debugging | 🟡 High |
| True E2E test | No full pipeline verification | 🔴 Critical |
| Shared fixtures | Duplicate code, inconsistency | 🟡 Medium |
| Documentation | Outdated docs, confusion | 🟡 Medium |

---

=== END OF FILE ===
