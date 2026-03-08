# ParkPartner Issues TODO

## Critical Issues

### 1. Empty Domain Files
- **Files**: `app/domain/models.py`, `app/domain/ports.py`, `app/domain/service.py`
- **Problem**: Completely empty. Project has hexagonal architecture structure but no actual domain logic implemented.
- **Priority**: High

### 2. Hardcoded Secret Token in Frontend
- **File**: `static/index.html` (line 78)
- **Problem**: `const SECRET_TOKEN = 'moi_secret_123';` exposes authentication token to any user viewing source.
- **Priority**: Critical
- **Fix**: Remove token from frontend, implement proper session-based auth or prompt user for token.

### 3. Config Mismatch
- **File**: `app/config.py` vs `.env.example`
- **Problem**: `config.py` loads `OLLAMA_*` variables, but `.env.example` specifies `DASHSCOPE_*` for Qwen API.
- **Priority**: Medium

## Code Quality Issues

### 4. No Validation on Audio File Size
- **File**: `app/adapters/api/routes.py`
- **Problem**: Could lead to memory issues with large uploads.
- **Priority**: Medium
- **Fix**: Add file size limit check (e.g., 10MB max).

### 5. Race Condition in Session State
- **File**: `app/core/state.py`
- **Problem**: `session_histories` is a global dict without thread/async safety.
- **Priority**: Medium
- **Fix**: Use `asyncio.Lock` or thread-safe data structure.

### 6. Unused Imports in `main.py`
- **File**: `main.py` (line 4)
- **Problem**: `from typing import Dict, List, Any` not used.
- **Priority**: Low
- **Fix**: Remove unused imports.

### 7. Missing Error Handling for File Response
- **File**: `app/adapters/api/routes.py`
- **Problem**: `transcribe_audio` and `synthesize_speech` return paths but don't validate file existence before `FileResponse`.
- **Priority**: Medium

### 8. TTS Voice Hardcoded
- **File**: `app/adapters/api/routes.py` (line 97)
- **Problem**: `"ru-RU-DmitryNeural"` is hardcoded instead of config.
- **Priority**: Low
- **Fix**: Add `TTS_VOICE` to config.

### 9. No Timeout Handling for Whisper
- **File**: `app/adapters/stt/whisper.py`
- **Problem**: 30s timeout may be insufficient for large audio files.
- **Priority**: Medium
- **Fix**: Increase timeout or add chunking for long audio.

### 10. Logging Sensitive Data
- **File**: `app/adapters/api/routes.py` (line 52)
- **Problem**: Session tokens partially logged (`session_id[:8]`), still exposes user tokens in logs.
- **Priority**: Medium
- **Fix**: Use session ID hash or UUID instead of token prefix.

## Architecture Issues

### 11. Business Logic in Routes
- **File**: `app/adapters/api/routes.py`
- **Problem**: Entire conversation flow is in routes instead of domain layer.
- **Priority**: High
- **Fix**: Move logic to `app/domain/service.py`.

### 12. No Dependency Injection
- **File**: `app/adapters/api/routes.py`
- **Problem**: Direct imports of adapters makes testing difficult.
- **Priority**: Medium
- **Fix**: Implement DI pattern for adapters (STT, LLM, TTS).

### 13. Architecture Diagram Mismatch - LLM Provider
- **File**: `docs/architecture.md` vs `app/adapters/api/routes.py`, `app/config.py`
- **Problem**: Diagram shows "Qwen/DashScope" (cloud API), but code uses **Ollama** (local LLM). Config has both `OLLAMA_*` and `DASHSCOPE_*` variables causing confusion.
- **Priority**: Medium
- **Fix**: Update diagram to show "Ollama (local)" OR switch implementation to DashScope.

### 14. Architecture Diagram Missing - ngrok Tunnel
- **File**: `docs/architecture.md` vs `main.py`
- **Problem**: Diagram includes ngrok HTTPS tunnel, but no ngrok integration exists in code.
- **Priority**: Low
- **Fix**: Either add ngrok integration or remove from diagram.

### 15. Architecture Diagram Missing - Domain Layer
- **File**: `docs/architecture.md`
- **Problem**: Diagram doesn't show the domain layer (`app/domain/`), which exists but is empty.
- **Priority**: Low
- **Fix**: Add domain layer to diagram and implement domain logic.

### 16. Update Architecture Documentation
- **File**: `docs/architecture.md`
- **Problem**: Only contains Mermaid diagram, no detailed documentation of components, data flow, or decisions.
- **Priority**: Medium
- **Fix**: Expand with component descriptions, API contracts, and architecture decisions.
