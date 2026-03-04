"""
Music-Off: Application entry point.
Starts the FastAPI server and opens the browser.
"""
import os
import shutil
import subprocess
import sys
import time
import webbrowser

# Fix Windows console encoding for unicode
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def check_dependencies():
    """Check that required dependencies are available."""
    print("=" * 50)
    print("  Music-Off: AI Music Remover")
    print("=" * 50)
    print()

    # Check FFmpeg
    if shutil.which("ffmpeg"):
        print("[OK] FFmpeg found")
    else:
        print("[!!] FFmpeg not found in PATH!")
        print("     Download from: https://ffmpeg.org/download.html")
        print("     Music-Off requires FFmpeg for video processing.")
        print()

    # Check PyTorch / CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"[OK] PyTorch with CUDA (GPU: {gpu_name})")
            print("     -> Processing will use GPU acceleration!")
        else:
            print("[OK] PyTorch (CPU mode)")
            print("     -> For faster processing, install CUDA-enabled PyTorch")
    except ImportError:
        print("[ERROR] PyTorch not found! Run: pip install torch torchaudio")
        sys.exit(1)

    # Check Demucs
    try:
        import demucs
        print("[OK] Demucs AI model available")
    except ImportError:
        print("[ERROR] Demucs not found! Run: pip install --no-deps demucs")
        sys.exit(1)

    print()


def main():
    check_dependencies()

    from app.config import HOST, PORT

    url = f"http://{HOST}:{PORT}"
    print(f"[>>] Starting server at {url}")
    print(f"     Press Ctrl+C to stop")
    print()

    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn
    import uvicorn
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
