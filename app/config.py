"""
Music-Off Configuration
"""
import os
import tempfile
from pathlib import Path

# --- Limits ---
MAX_DURATION_SECONDS = 1800  # 30 minutes
MAX_FILE_SIZE_MB = 1024  # 1 GB max upload size
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Supported formats ---
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"}
SUPPORTED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

# --- Directories ---
TEMP_DIR = Path(tempfile.gettempdir()) / "music-off"
TEMP_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = TEMP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

PROCESSING_DIR = TEMP_DIR / "processing"
PROCESSING_DIR.mkdir(exist_ok=True)

OUTPUT_DIR = TEMP_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- Demucs ---
DEMUCS_MODEL = "htdemucs"
# Stems to KEEP (vocals = speech/singing)
STEMS_TO_KEEP = ["vocals"]
# Stems to DISCARD (drums, bass, other = music/instruments)
STEMS_TO_DISCARD = ["drums", "bass", "other"]

# --- Server ---
HOST = "127.0.0.1"
PORT = 8765
