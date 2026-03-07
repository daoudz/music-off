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
HOST = "0.0.0.0"  # Listen on all interfaces (LAN accessible)
PORT = 8765

# --- Job Queue ---
MAX_CONCURRENT_JOBS = 1  # Process one file at a time to avoid overloading

# --- File Retention ---
FILE_RETENTION_SECONDS = 3600  # 1 hour — output/processing files deleted after this
CLEANUP_INTERVAL_SECONDS = 300  # Check every 5 minutes
