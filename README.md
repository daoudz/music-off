# 🎵 Music-Off: AI Music Remover

Remove music from audio and video files using AI, while preserving voice and sound effects.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Demucs](https://img.shields.io/badge/AI-Demucs%20by%20Meta-purple)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)

## Features

- 🧠 **AI-Powered** — Uses Meta's Demucs model for state-of-the-art music source separation
- 🎬 **Video + Audio** — Supports MP4, MKV, AVI, MOV, MP3, WAV, FLAC, and more
- ⏱️ **Up to 10 minutes** — Process media files up to 10 minutes long
- 🎯 **Preserves Voice & SFX** — Removes only music while keeping dialogue and sound effects
- 📂 **Custom Output** — Save results to any local directory
- ⚡ **GPU Accelerated** — Uses CUDA if available for faster processing
- 🖥️ **Beautiful UI** — Premium dark theme with drag-and-drop upload

## Quick Start

### Prerequisites
- [Python 3.9+](https://python.org/downloads)
- [FFmpeg](https://ffmpeg.org/download.html) — required for video processing

### Setup

```bash
# Run the setup script (Windows)
setup.bat

# Or manual setup:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
venv\Scripts\activate
python start.py
```

The app opens in your browser at `http://127.0.0.1:8765`

## How It Works

1. **Upload** — Drag & drop or select an audio/video file
2. **AI Processing** — Demucs separates audio into stems (vocals, drums, bass, other)
3. **Smart Merge** — Keeps vocals + other (SFX/ambient), discards drums + bass (music)
4. **Output** — Saves the music-free result to your chosen directory

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Model | Demucs (htdemucs) by Meta |
| Backend | Python + FastAPI |
| Media | FFmpeg |
| Frontend | Vanilla HTML/CSS/JS |

## License

MIT
