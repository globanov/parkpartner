# ParkPartner 🎙️

Voice-based AI assistant for park visitors (Russian). Speak via mobile web interface, get spoken responses.

**Stack:** FastAPI + Whisper (STT) + Ollama (qwen2.5:3b) + Edge TTS + Vanilla JS frontend.

## 🚀 Quick Start

### Prerequisites

**Python 3.12**, **Ollama**, **FFmpeg**

```bash
# Install Ollama (macOS)
brew install ollama
ollama serve
ollama pull qwen2.5:3b

# Install FFmpeg
brew install ffmpeg  # macOS
sudo apt-get install ffmpeg  # Ubuntu/Debian
```

### Installation

```bash
git clone <repository-url>
cd parkpartner
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit if needed
```

### Start Server

```bash
python parkpartner.py
```

Open http://localhost:8000

### Mobile Access (HTTPS)

```bash
python start_parkpartner_with_tunnel.py
```

Copy the https://*.localhost.run URL to access from iPhone.

### Stop Server

```bash
# Press Ctrl+C in terminal
# or
pkill -f "parkpartner:app"  # macOS/Linux
```

## 🛠 Development

### Test Commands

```bash
# Run E2E tests (browser UI + true E2E)
python run_e2e_tests.py -t "user_journey" --headed

# Run specific test
pytest tests/ -v -k "smoke"
```

### Project Structure

```
parkpartner/
├── parkpartner.py              # FastAPI application entry point
├── start_parkpartner_with_tunnel.py  # Server + HTTPS tunnel
├── run_e2e_tests.py            # E2E test runner with auto server management
├── app/
│   ├── adapters/api/routes.py  # HTTP API routes
│   ├── adapters/llm/           # Ollama LLM adapter
│   ├── adapters/stt/           # Whisper STT adapter
│   ├── adapters/tts/           # Edge TTS adapter
│   ├── core/                   # Dependencies, state management
│   ├── domain/                 # Business logic (ports.py, service.py)
│   └── config.py               # Environment-based configuration
├── static/index.html           # Frontend (vanilla JS PWA)
├── tests/
│   ├── system/conftest.py      # E2E test fixtures
│   └── system/test_e2e_002_true_e2e.py  # True E2E test
├── logs/server/                # Server logs
├── logs/tests/system/          # System test logs
└── docs/                       # Architecture, testing, E2E docs
```

### Guidelines

- **Logging:** use `app.config.setup_logging()`
- **Commits:** match existing style (`feat:`, `fix:`, `chore:`)
- **Tests:** verify both localhost + tunnel modes

## 📚 Documentation

- [Architecture](docs/architecture.md) - System design
- [Testing Guide](docs/TESTING.md) - How to run/write tests
- [E2E Tests](docs/E2E.md) - Test scenarios

## ⚠️ Known Limitations

- All users share one "anonymous" session (no user isolation)
- CORS allows all origins (ok for local dev, restrict in production)
- MediaRecorder mock in `tests/system/conftest.py` — don't call `onstop` manually

---

**License:** MIT
