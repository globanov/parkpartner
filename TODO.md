# ParkPartner Issues TODO

## Remaining Issues (Optional Enhancements)

### 1. Improve Session Management
- **Issue**: All users share "anonymous" session
- **Impact**: No user isolation
- **Priority**: Low (acceptable for demo/MVP)

### 2. Restrict CORS Origins
- **File**: `main.py`
- **Issue**: `allow_origins=["*"]`
- **Priority**: Low (acceptable for local development)

---

## Summary

| Category | Status |
|----------|--------|
| **Code Quality** | ✅ All ruff checks passing |
| **Formatting** | ✅ 16 files formatted |
| **CI/CD** | ✅ Updated to use ruff + pytest |
| **Tests** | ✅ 22 tests passing |
| **Documentation** | ✅ README + architecture diagram |
| **Configuration** | ✅ All hardcoded values moved to config |
