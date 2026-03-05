"""
Music-Off: Core audio/video processing pipeline.
Handles Demucs separation, stem merging, and video remuxing.
"""
import asyncio
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import torch

from app.config import (
    DEMUCS_MODEL,
    MAX_CONCURRENT_JOBS,
    MAX_DURATION_SECONDS,
    OUTPUT_DIR,
    PROCESSING_DIR,
    STEMS_TO_KEEP,
    SUPPORTED_AUDIO_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    UPLOAD_DIR,
)

# --- Job tracking ---
jobs: dict = {}

# --- Server stats ---
server_stats = {
    "started_at": time.time(),
    "total_processed": 0,
    "total_errors": 0,
    "bytes_uploaded": 0,
    "bytes_downloaded": 0,
    "history": [],  # [{timestamp, job_id, filename, status, duration_sec, output_size}]
}

# --- Processing queue (semaphore) ---
_processing_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    """Lazy-init semaphore (must be created inside a running event loop)."""
    global _processing_semaphore
    if _processing_semaphore is None:
        _processing_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)
    return _processing_semaphore


def _update_queue_positions():
    """Recalculate queue positions for all waiting jobs."""
    queued = [
        (jid, j) for jid, j in jobs.items()
        if j["status"] == "queued"
    ]
    # Sort by creation time
    queued.sort(key=lambda x: x[1]["created_at"])
    for pos, (jid, j) in enumerate(queued, start=1):
        j["queue_position"] = pos
        j["message"] = f"Queued for processing (position {pos})..."

# --- Custom FFmpeg path ---
_custom_ffmpeg_dir: str | None = None


def set_custom_ffmpeg_path(path: str):
    """Set a custom directory where FFmpeg binaries are located."""
    global _custom_ffmpeg_dir
    _custom_ffmpeg_dir = path


def get_ffmpeg_path() -> str:
    """Find FFmpeg in custom path, PATH, or common locations."""
    # 1. Check custom path first
    if _custom_ffmpeg_dir:
        for name in ("ffmpeg.exe", "ffmpeg"):
            p = os.path.join(_custom_ffmpeg_dir, name)
            if os.path.exists(p):
                return p

    # 2. Auto-detect via PATH
    if shutil.which("ffmpeg"):
        return "ffmpeg"

    # 3. Common locations
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    raise RuntimeError(
        "FFmpeg not found. Please install FFmpeg and add it to your PATH.\n"
        "Download: https://ffmpeg.org/download.html"
    )


def get_media_duration(file_path: str) -> float:
    """Get duration of a media file in seconds using ffprobe."""
    ffmpeg = get_ffmpeg_path()
    ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
    if not shutil.which(ffprobe) and not os.path.exists(ffprobe):
        ffprobe = "ffprobe"

    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


def is_video_file(file_path: str) -> bool:
    """Check if file is a video based on extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def is_audio_file(file_path: str) -> bool:
    """Check if file is audio based on extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS


def extract_audio_from_video(video_path: str, output_audio_path: str) -> bool:
    """Extract audio track from video file using FFmpeg."""
    ffmpeg = get_ffmpeg_path()
    try:
        subprocess.run(
            [
                ffmpeg,
                "-i", str(video_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                "-y",
                str(output_audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=300,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg audio extraction failed: {e.stderr}")
        return False


def remux_audio_with_video(
    original_video: str, new_audio: str, output_path: str
) -> bool:
    """Replace audio track in video with new audio using FFmpeg."""
    ffmpeg = get_ffmpeg_path()
    try:
        subprocess.run(
            [
                ffmpeg,
                "-i", str(original_video),
                "-i", str(new_audio),
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg remux failed: {e.stderr}")
        return False


def _load_audio_as_tensor(audio_path: str, target_sr: int, target_channels: int):
    """Load audio file as a torch tensor using soundfile + numpy resampling."""
    data, sr = sf.read(audio_path, dtype="float32", always_2d=True)
    # data shape: (samples, channels) -> convert to (channels, samples)
    wav = torch.from_numpy(data.T)

    # Resample if needed
    if sr != target_sr:
        from scipy.signal import resample as scipy_resample
        num_samples = int(wav.shape[1] * target_sr / sr)
        resampled = np.zeros((wav.shape[0], num_samples), dtype=np.float32)
        for ch in range(wav.shape[0]):
            resampled[ch] = scipy_resample(wav[ch].numpy(), num_samples).astype(np.float32)
        wav = torch.from_numpy(resampled)

    # Ensure correct number of channels
    if wav.shape[0] == 1 and target_channels == 2:
        wav = wav.repeat(2, 1)
    elif wav.shape[0] > target_channels:
        wav = wav[:target_channels]

    return wav


def run_demucs_separation(audio_path: str, output_dir: str) -> Optional[str]:
    """
    Run Demucs source separation on an audio file.
    Returns path to the separation output directory.
    """
    try:
        from demucs.apply import apply_model
        from demucs.pretrained import get_model

        # Load model
        model = get_model(DEMUCS_MODEL)
        model.eval()

        # Use GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)

        # Load audio using soundfile (no lameenc/torchcodec needed)
        wav = _load_audio_as_tensor(audio_path, model.samplerate, model.audio_channels)

        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        wav = wav.to(device)

        # Separate
        sources = apply_model(model, wav[None], device=device, progress=True)[0]
        sources = sources * ref.std() + ref.mean()

        # Save stems
        stem_dir = Path(output_dir) / "stems"
        stem_dir.mkdir(parents=True, exist_ok=True)

        source_names = model.sources
        for i, name in enumerate(source_names):
            stem_path = stem_dir / f"{name}.wav"
            audio_data = sources[i].cpu().numpy()
            sf.write(str(stem_path), audio_data.T, model.samplerate)

        return str(stem_dir)

    except Exception as e:
        print(f"Demucs separation failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: use command-line demucs
        return run_demucs_cli(audio_path, output_dir)


def run_demucs_cli(audio_path: str, output_dir: str) -> Optional[str]:
    """Fallback: run Demucs via command line."""
    try:
        result = subprocess.run(
            [
                "python", "-m", "demucs",
                "-n", DEMUCS_MODEL,
                "--out", str(output_dir),
                "--two-stems=vocals",  # Not used but ensures model loads
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 min timeout
        )

        if result.returncode != 0:
            # Try without two-stems
            result = subprocess.run(
                [
                    "python", "-m", "demucs",
                    "-n", DEMUCS_MODEL,
                    "--out", str(output_dir),
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=1800,
            )

        # Find output directory
        audio_name = Path(audio_path).stem
        stem_dir = Path(output_dir) / DEMUCS_MODEL / audio_name
        if stem_dir.exists():
            return str(stem_dir)

        # Search for stems
        for d in Path(output_dir).rglob("vocals.wav"):
            return str(d.parent)

        return None

    except Exception as e:
        print(f"Demucs CLI failed: {e}")
        return None


def merge_stems(stem_dir: str, output_path: str, stems_to_keep: list) -> bool:
    """Merge selected stems into a single audio file."""
    try:
        mixed = None
        sr = None

        for stem_name in stems_to_keep:
            stem_path = Path(stem_dir) / f"{stem_name}.wav"
            if not stem_path.exists():
                print(f"Warning: stem {stem_name}.wav not found, skipping")
                continue

            data, sample_rate = sf.read(str(stem_path))
            sr = sample_rate

            if mixed is None:
                mixed = data.astype(np.float64)
            else:
                # Ensure same length
                min_len = min(len(mixed), len(data))
                mixed = mixed[:min_len] + data[:min_len].astype(np.float64)

        if mixed is None:
            return False

        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 0.99:
            mixed = mixed * 0.95 / max_val

        sf.write(output_path, mixed.astype(np.float32), sr)
        return True

    except Exception as e:
        print(f"Stem merging failed: {e}")
        return False


async def process_file(job_id: str, file_path: str, custom_output_dir: Optional[str] = None):
    """
    Main processing pipeline. Waits in queue, then processes.
    """
    job = jobs[job_id]
    _update_queue_positions()

    # Wait for our turn in the queue
    sem = _get_semaphore()
    await sem.acquire()

    try:
        await _run_processing(job_id, file_path, custom_output_dir)
    finally:
        sem.release()
        _update_queue_positions()


async def _run_processing(job_id: str, file_path: str, custom_output_dir: Optional[str] = None):
    """
    Actual processing logic, runs after semaphore is acquired.
    """
    job = jobs[job_id]
    job["status"] = "processing"
    job["progress"] = 5
    job["message"] = "Validating file..."
    job["queue_position"] = 0

    try:
        original_path = Path(file_path)
        is_video = is_video_file(file_path)
        job_dir = PROCESSING_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Check duration
        job["progress"] = 10
        job["message"] = "Checking file duration..."

        duration = await asyncio.to_thread(get_media_duration, file_path)
        if duration > MAX_DURATION_SECONDS:
            job["status"] = "error"
            job["message"] = f"File is {duration/60:.1f} minutes long. Maximum allowed is {MAX_DURATION_SECONDS/60:.0f} minutes."
            return

        job["duration"] = duration

        # Step 2: Extract audio if video
        audio_path = file_path
        if is_video:
            job["progress"] = 15
            job["message"] = "Extracting audio from video..."
            extracted_audio = str(job_dir / "extracted_audio.wav")
            success = await asyncio.to_thread(
                extract_audio_from_video, file_path, extracted_audio
            )
            if not success:
                job["status"] = "error"
                job["message"] = "Failed to extract audio from video. Is FFmpeg installed?"
                return
            audio_path = extracted_audio

        # Step 3: Run Demucs separation
        job["progress"] = 25
        job["message"] = "🧠 AI is separating audio stems... This may take a few minutes."

        stem_dir = await asyncio.to_thread(
            run_demucs_separation, audio_path, str(job_dir)
        )

        if not stem_dir:
            job["status"] = "error"
            job["message"] = "AI separation failed. Please check that Demucs is installed correctly."
            return

        job["progress"] = 75
        job["message"] = "Merging stems (removing music)..."

        # Step 4: Merge desired stems
        merged_audio = str(job_dir / "merged_no_music.wav")
        success = await asyncio.to_thread(
            merge_stems, stem_dir, merged_audio, STEMS_TO_KEEP
        )
        if not success:
            job["status"] = "error"
            job["message"] = "Failed to merge audio stems."
            return

        # Step 5: Create final output
        job["progress"] = 85
        job["message"] = "Creating final output..."

        # Determine output directory
        out_dir = Path(custom_output_dir) if custom_output_dir else OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_name = f"{original_path.stem}_no_music_{timestamp}"

        if is_video:
            # Remux: replace audio in the original video
            output_file = str(out_dir / f"{output_name}{original_path.suffix}")
            success = await asyncio.to_thread(
                remux_audio_with_video, file_path, merged_audio, output_file
            )
            if not success:
                job["status"] = "error"
                job["message"] = "Failed to remux video with processed audio."
                return
        else:
            # Audio only: save as WAV
            output_file = str(out_dir / f"{output_name}.wav")
            shutil.copy2(merged_audio, output_file)

        # Done!
        job["progress"] = 100
        job["status"] = "completed"
        job["message"] = "✅ Music removed successfully!"
        job["output_file"] = output_file
        job["output_filename"] = Path(output_file).name
        job["completed_at"] = time.time()

        # Record stats
        output_size = Path(output_file).stat().st_size if Path(output_file).exists() else 0
        job["output_size"] = output_size
        server_stats["total_processed"] += 1
        server_stats["history"].append({
            "timestamp": time.time(),
            "job_id": job_id,
            "filename": job["filename"],
            "status": "completed",
            "duration_sec": round(time.time() - job["created_at"], 1),
            "output_size": output_size,
        })
        # Keep last 100 history entries
        if len(server_stats["history"]) > 100:
            server_stats["history"] = server_stats["history"][-100:]

    except Exception as e:
        job["status"] = "error"
        job["message"] = f"Processing failed: {str(e)}"
        job["completed_at"] = time.time()
        server_stats["total_errors"] += 1
        server_stats["history"].append({
            "timestamp": time.time(),
            "job_id": job_id,
            "filename": job["filename"],
            "status": "error",
            "duration_sec": round(time.time() - job["created_at"], 1),
            "output_size": 0,
        })
        print(f"Job {job_id} error: {e}")

    finally:
        # Clean up uploaded file
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
        except Exception:
            pass


def create_job(filename: str) -> str:
    """Create a new processing job and return its ID."""
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "id": job_id,
        "filename": filename,
        "status": "queued",
        "progress": 0,
        "message": "Queued for processing...",
        "output_file": None,
        "output_filename": None,
        "duration": None,
        "created_at": time.time(),
        "completed_at": None,
        "queue_position": 0,
    }
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    """Get job status by ID."""
    return jobs.get(job_id)
