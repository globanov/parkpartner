# ParkPartner 🎙️

A voice-based AI assistant for park walks. Speak to it via a mobile-friendly web interface, and it responds with synthesized speech.

## Features

- 🎤 **Voice-first interface** - Hold-to-talk interaction
- 🧠 **Local AI** - Runs entirely on your machine (no cloud APIs)
- 🗣️ **Russian language** - Optimized for Russian speech
- 💬 **Conversation history** - Remembers last 6 messages
- 📱 **Mobile-friendly** - Works on iPhone Safari as PWA

## Architecture

See [Architecture Documentation](docs/architecture.md) for detailed system design, data flow, and component descriptions.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.12) |
| STT | OpenAI Whisper (local) |
| LLM | Ollama with qwen2.5:3b |
| TTS | Edge TTS (free, no API key) |
| Frontend | Vanilla JS + Web Audio API |

## Prerequisites

- **Python 3.11+**
- **Ollama** - Install from [ollama.ai](https://ollama.ai)
- **FFmpeg** - Required for audio processing

### Install Ollama and Model

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull the model
ollama pull qwen2.5:3b
```

### Install FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg
```

## Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd parkpartner
```

2. **Create virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` with your preferences:

```env
# STT Settings (Local Whisper)
STT_PROVIDER=local
WHISPER_MODEL=small
WHISPER_LANGUAGE=ru

# LLM Settings (Ollama - Local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

# TTS Settings (Edge - Free)
TTS_PROVIDER=edge
TTS_VOICE=ru-RU-DmitryNeural
```

## Usage

1. **Start the server**

```bash
python main.py
```

2. **Open in browser**

Navigate to `http://localhost:8000`

3. **Use the interface**

- Click and hold the **🎤 Hold to Talk** button
- Speak your message
- Release to send
- Listen to the AI response

## Configuration Options

### Whisper Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 75 MB | Fastest | Lower |
| `base` | 142 MB | Fast | Good |
| `small` | 244 MB | Medium | Better |
| `medium` | 769 MB | Slow | Best |

### TTS Voices (Russian)

- `ru-RU-DmitryNeural` (Male)
- `ru-RU-SvetlanaNeural` (Female)

### Available LLM Models

Any Ollama model works. Recommended:
- `qwen2.5:3b` - Balanced speed/quality
- `llama3.2:3b` - Alternative option
- `mistral:7b` - Higher quality, slower

## API Endpoints

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:8000/health
# {"status": "ok", "version": "0.1.0"}
```

### `POST /process`

Process audio and get response.

```bash
curl -X POST http://localhost:8000/process \
  -F "file=@recording.webm" \
  --output response.mp3
```

### `GET /`

Serve the frontend HTML interface.

## Development

### Run linter

```bash
ruff check .
```

### Format code

```bash
ruff format .
```

### Run tests

```bash
pytest
```

## Troubleshooting

### "Ollama service unavailable"

- Ensure Ollama is running: `ollama serve`
- Check model is pulled: `ollama pull qwen2.5:3b`

### "No speech detected"

- Speak clearly and louder
- Check microphone permissions in browser
- Try a different browser (Safari recommended on iOS)

### Audio playback issues on iOS

- Ensure volume is up
- iOS may block autoplay - click the play button when shown
- Use headphones for better experience

## License

MIT License

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech-to-text
- [Ollama](https://ollama.ai) - Local LLM
- [Edge TTS](https://github.com/rany2/edge-tts) - Text-to-speech
- [FastAPI](https://fastapi.tiangolo.com) - Web framework
