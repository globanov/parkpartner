# 🏗️ ParkPartner

```mermaid
flowchart
    subgraph Client["📱 Client (iPhone)"]
        Mic[🎤 Microphone]
        Browser[iPhone Safari PWA]
        Speaker[🔊 Speaker]
    end

    subgraph Tunnel["🌐 ngrok Tunnel"]
        HTTPS[🔒 HTTPS Endpoint]
    end

    subgraph Server["🏠 Server (Mac)"]
        API[🐍 FastAPI main.py]
        History[💾 Dialog History]
    end

    subgraph External["🔌 External APIs"]
        Whisper[👂 Groq Whisper STT]
        LLM[🧠 Qwen LLM DashScope]
        TTS[🗣️ Edge TTS Free]
    end

    Mic --> Browser
    Browser <-->|HTTPS| HTTPS
    HTTPS <--> API
    API -.-> History
    API <-->|audio| Whisper
    API <-->|text| LLM
    API <-->|audio| TTS
    Browser --> Speaker

    style Client fill:#1e3a5f,stroke:#4a9eff,stroke-width:2px,color:#fff
    style Tunnel fill:#2d5016,stroke:#7ec850,stroke-width:2px,color:#fff
    style Server fill:#50162d,stroke:#c8507e,stroke-width:2px,color:#fff
    style External fill:#4a3c16,stroke:#d4af37,stroke-width:2px,color:#fff