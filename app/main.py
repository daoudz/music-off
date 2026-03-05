"""
Music-Off: FastAPI Server
Serves the API and frontend for the music removal app.
"""
import asyncio
import os
import shutil
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import (
    CLEANUP_INTERVAL_SECONDS,
    FILE_RETENTION_SECONDS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    OUTPUT_DIR,
    PROCESSING_DIR,
    SUPPORTED_EXTENSIONS,
    UPLOAD_DIR,
)
from app.processor import create_job, get_job, jobs, process_file, server_stats

app = FastAPI(title="Music-Off", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# User's selected output directory (persisted in memory)
user_output_dir: dict = {"path": None}

# Custom FFmpeg path (None = auto-detect)
custom_ffmpeg_path: dict = {"path": None}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a media file for music removal processing."""
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{os.urandom(8).hex()}_{file.filename}"

    try:
        total_size = 0
        with open(upload_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    f.close()
                    upload_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.",
                    )
                f.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Track upload bandwidth
    server_stats["bytes_uploaded"] += total_size

    # Create processing job
    job_id = create_job(file.filename)

    # Start background processing
    asyncio.create_task(
        process_file(job_id, str(upload_path), user_output_dir.get("path"))
    )

    return {"job_id": job_id, "filename": file.filename, "message": "Processing started"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Get the processing status of a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    """Download the processed file."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    output_file = job.get("output_file")
    if not output_file or not Path(output_file).exists():
        raise HTTPException(status_code=404, detail="Output file not found")

    # Track download bandwidth
    output_size = Path(output_file).stat().st_size
    server_stats["bytes_downloaded"] += output_size

    return FileResponse(
        path=output_file,
        filename=job["output_filename"],
        media_type="application/octet-stream",
    )


@app.post("/api/set-output-dir")
async def set_output_dir(directory: str = Form(...)):
    """Set the output directory for processed files."""
    dir_path = Path(directory)
    if not dir_path.exists():
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Cannot create directory: {str(e)}"
            )

    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    user_output_dir["path"] = str(dir_path)
    return {"message": f"Output directory set to: {directory}", "path": str(dir_path)}


@app.get("/api/output-dir")
async def get_output_dir():
    """Get the current output directory."""
    return {"path": user_output_dir.get("path")}


@app.get("/api/browse-folder")
async def browse_folder():
    """Open a native folder picker dialog and return the selected path."""
    import asyncio

    def _pick_folder():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=user_output_dir.get("path") or os.path.expanduser("~"),
        )
        root.destroy()
        return folder

    folder = await asyncio.to_thread(_pick_folder)

    if folder:
        user_output_dir["path"] = folder
        return {"path": folder, "selected": True}
    return {"path": user_output_dir.get("path"), "selected": False}


@app.get("/api/browse-ffmpeg")
async def browse_ffmpeg():
    """Open a native folder picker for FFmpeg bin directory."""
    import asyncio

    def _pick_folder():
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(
            title="Select FFmpeg bin Folder",
            initialdir=custom_ffmpeg_path.get("path") or "C:\\",
        )
        root.destroy()
        return folder

    folder = await asyncio.to_thread(_pick_folder)

    if folder:
        ffmpeg_exe = Path(folder) / "ffmpeg.exe"
        if not ffmpeg_exe.exists():
            # Also check without .exe (Linux/Mac)
            ffmpeg_plain = Path(folder) / "ffmpeg"
            if not ffmpeg_plain.exists():
                return {"path": folder, "selected": True, "warning": "ffmpeg not found in this folder"}

        custom_ffmpeg_path["path"] = folder
        # Update processor's custom path
        from app.processor import set_custom_ffmpeg_path
        set_custom_ffmpeg_path(folder)
        return {"path": folder, "selected": True}
    return {"path": custom_ffmpeg_path.get("path"), "selected": False}


@app.post("/api/set-ffmpeg-path")
async def set_ffmpeg_path(ffmpeg_path: str = Form(...)):
    """Set a custom FFmpeg bin directory path."""
    dir_path = Path(ffmpeg_path)
    if not dir_path.exists():
        raise HTTPException(status_code=400, detail=f"Directory does not exist: {ffmpeg_path}")
    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # Check if ffmpeg exists in the directory
    ffmpeg_exe = dir_path / "ffmpeg.exe"
    ffmpeg_plain = dir_path / "ffmpeg"
    if not ffmpeg_exe.exists() and not ffmpeg_plain.exists():
        raise HTTPException(status_code=400, detail="ffmpeg executable not found in this directory")

    custom_ffmpeg_path["path"] = str(dir_path)
    from app.processor import set_custom_ffmpeg_path
    set_custom_ffmpeg_path(str(dir_path))

    return {"message": f"FFmpeg path set to: {ffmpeg_path}", "path": str(dir_path)}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    # Check FFmpeg: custom path first, then auto-detect
    ffmpeg_available = False
    if custom_ffmpeg_path.get("path"):
        ffmpeg_dir = Path(custom_ffmpeg_path["path"])
        ffmpeg_available = (ffmpeg_dir / "ffmpeg.exe").exists() or (ffmpeg_dir / "ffmpeg").exists()
    if not ffmpeg_available:
        ffmpeg_available = shutil.which("ffmpeg") is not None

    try:
        import torch
        cuda_available = torch.cuda.is_available()
        device = "CUDA (GPU)" if cuda_available else "CPU"
    except ImportError:
        cuda_available = False
        device = "Unknown"

    return {
        "status": "ok",
        "ffmpeg": ffmpeg_available,
        "device": device,
        "cuda": cuda_available,
    }


@app.get("/api/queue-status")
async def queue_status():
    """Get current queue information."""
    active = sum(1 for j in jobs.values() if j["status"] == "processing")
    queued = sum(1 for j in jobs.values() if j["status"] == "queued")
    completed = sum(1 for j in jobs.values() if j["status"] == "completed")
    return {
        "active": active,
        "queued": queued,
        "completed": completed,
        "total": len(jobs),
    }


# --- Background cleanup task ---
async def cleanup_old_files():
    """Periodically delete expired output/processing files and purge old job records."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        now = time.time()
        expired_job_ids = []

        for job_id, job in list(jobs.items()):
            completed_at = job.get("completed_at")
            if completed_at is None:
                continue  # Still running or queued
            if now - completed_at < FILE_RETENTION_SECONDS:
                continue  # Not expired yet

            # Delete output file
            output_file = job.get("output_file")
            if output_file and Path(output_file).exists():
                try:
                    Path(output_file).unlink()
                    print(f"[Cleanup] Deleted output: {output_file}")
                except Exception as e:
                    print(f"[Cleanup] Failed to delete output {output_file}: {e}")

            # Delete processing temp directory
            job_proc_dir = PROCESSING_DIR / job_id
            if job_proc_dir.exists():
                try:
                    shutil.rmtree(str(job_proc_dir))
                    print(f"[Cleanup] Deleted processing dir: {job_proc_dir}")
                except Exception as e:
                    print(f"[Cleanup] Failed to delete dir {job_proc_dir}: {e}")

            expired_job_ids.append(job_id)

        # Remove expired jobs from memory
        for job_id in expired_job_ids:
            del jobs[job_id]

        if expired_job_ids:
            print(f"[Cleanup] Purged {len(expired_job_ids)} expired job(s)")


@app.on_event("startup")
async def startup_event():
    """Start background cleanup task when server starts."""
    asyncio.create_task(cleanup_old_files())


@app.get("/api/metrics")
async def get_metrics():
    """Full metrics endpoint for the admin dashboard."""
    import psutil

    now = time.time()
    uptime = now - server_stats["started_at"]

    # System stats
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()

    # Disk usage for temp dir
    try:
        from app.config import TEMP_DIR
        temp_size = sum(
            f.stat().st_size for f in Path(str(TEMP_DIR)).rglob("*") if f.is_file()
        )
    except Exception:
        temp_size = 0

    # Output dir size
    try:
        output_size = sum(
            f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()
        )
    except Exception:
        output_size = 0

    # Job counts
    active = sum(1 for j in jobs.values() if j["status"] == "processing")
    queued = sum(1 for j in jobs.values() if j["status"] == "queued")
    completed_now = sum(1 for j in jobs.values() if j["status"] == "completed")
    errored = sum(1 for j in jobs.values() if j["status"] == "error")

    # Active jobs detail
    active_jobs = []
    for jid, j in jobs.items():
        if j["status"] in ("processing", "queued"):
            active_jobs.append({
                "id": jid,
                "filename": j["filename"],
                "status": j["status"],
                "progress": j["progress"],
                "queue_position": j.get("queue_position", 0),
                "elapsed": round(now - j["created_at"], 1),
            })

    return {
        "uptime_seconds": round(uptime, 0),
        "system": {
            "cpu_percent": cpu_percent,
            "ram_total_gb": round(mem.total / (1024**3), 2),
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_percent": mem.percent,
        },
        "storage": {
            "temp_dir_bytes": temp_size,
            "output_dir_bytes": output_size,
            "total_bytes": temp_size + output_size,
        },
        "queue": {
            "active": active,
            "queued": queued,
            "completed": completed_now,
            "errored": errored,
        },
        "totals": {
            "processed": server_stats["total_processed"],
            "errors": server_stats["total_errors"],
            "bytes_uploaded": server_stats["bytes_uploaded"],
            "bytes_downloaded": server_stats["bytes_downloaded"],
        },
        "history": server_stats["history"][-50:],
        "active_jobs": active_jobs,
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the admin dashboard page."""
    dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    # Fallback: serve from frontend directory directly
    frontend_dev = Path(__file__).parent.parent / "frontend"
    if frontend_dev.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dev), html=True), name="frontend")
