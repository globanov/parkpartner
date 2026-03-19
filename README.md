# ParkPartner 🎙️

Voice-based AI assistant for park walks. Speak via mobile web interface, get spoken responses.

## Quick Start

### Prerequisites

**Python 3.11+**, **Ollama**, **FFmpeg**

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
./start_parkpartner_with_tunnel.sh
```

Copy the https://*.localhost.run URL to access from iPhone.

### Stop Server

```bash
# Press Ctrl+C in terminal
# or
pkill -f "parkpartner:app"  # macOS/Linux
```

## Development

See [Testing Guide](docs/TESTING.md) for test commands and troubleshooting.

## Troubleshooting

See [Testing Guide](docs/TESTING.md) for test-related issues.

**"Ollama service unavailable"**
- Run: `ollama serve`
- Pull model: `ollama pull qwen2.5:3b`

**"No speech detected"**
- Speak clearly and louder
- Check microphone permissions in browser
- Try Safari on iOS

**Audio playback issues on iOS**
- Turn volume up
- Click play button if autoplay blocked
- Use headphones

## Known Limitations

- All users share one "anonymous" session (no user isolation)
- CORS allows all origins (ok for local dev, restrict in production)

## Documentation

- [Architecture](docs/architecture.md) - System design
- [Testing Guide](docs/TESTING.md) - How to run/write tests
- [E2E Tests](docs/E2E.md) - Test scenarios

---

**License:** MIT
