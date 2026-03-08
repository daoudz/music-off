"""
Music-Off: FastAPI Server
Serves the API and frontend for the music removal app.
"""
import asyncio
import os
import shutil
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
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


# --- Dashboard Auth ---
DASH_PASSWORD = "@12345678"
AUTH_STATE = {}  # ip: {"attempts": int, "blocked_until": float}

def _check_ip_blocked(client_ip: str) -> bool:
    state = AUTH_STATE.get(client_ip)
    if not state: return False
    return time.time() < state["blocked_until"]

def _record_failed_attempt(client_ip: str):
    now = time.time()
    state = AUTH_STATE.get(client_ip, {"attempts": 0, "blocked_until": 0})
    if now >= state["blocked_until"]:
        state["attempts"] += 1
        if state["attempts"] >= 3:
            state["blocked_until"] = now + 60  # Block for 1 min
            state["attempts"] = 0
    AUTH_STATE[client_ip] = state

def _reset_attempts(client_ip: str):
    if client_ip in AUTH_STATE:
        AUTH_STATE[client_ip] = {"attempts": 0, "blocked_until": 0}



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
        process_file(job_id, str(upload_path))
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
async def get_metrics(request: Request):
    """Full metrics endpoint for the admin dashboard."""
    client_ip = request.client.host
    if _check_ip_blocked(client_ip):
        raise HTTPException(status_code=429, detail="Blocked due to too many failed attempts")
        
    auth_cookie = request.cookies.get("dash_auth")
    if auth_cookie != DASH_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
async def dashboard_page(request: Request):
    """Serve the admin dashboard page."""
    client_ip = request.client.host
    if _check_ip_blocked(client_ip):
        return HTMLResponse("<h1>Too many failed attempts. Try again in 1 minute.</h1>", status_code=429)
        
    auth_cookie = request.cookies.get("dash_auth")
    if auth_cookie != DASH_PASSWORD:
        login_html = """
        <!DOCTYPE html>
        <html><head><title>Dashboard Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { background: #0a0a0f; color: white; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            form { background: rgba(18, 18, 30, 0.65); padding: 40px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); text-align: center; width: 100%; max-width: 400px; box-sizing: border-box; }
            h2 { margin-top: 0; }
            input[type=password] { padding: 12px; border-radius: 8px; border: 1px solid #333; background: #1a1a24; color: white; width: 100%; box-sizing: border-box; margin-bottom: 20px; outline: none; transition: 0.3s; }
            input[type=password]:focus { border-color: #a855f7; }
            button { background: linear-gradient(135deg, #a855f7, #6366f1); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; transition: 0.3s; }
            button:hover { opacity: 0.9; transform: translateY(-1px); }
        </style>
        </head><body>
        <form method="POST" action="/dashboard/login">
            <h2>Dashboard Access</h2>
            <p style="color:#9898b0; font-size: 0.9em; margin-bottom: 24px;">Please enter the password to view metrics.</p>
            <input type="password" name="password" placeholder="Password" required autofocus>
            <button type="submit">Unlock Dashboard</button>
        </form>
        </body></html>
        """
        return HTMLResponse(content=login_html)

    dashboard_path = Path(__file__).parent.parent / "frontend" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


@app.post("/dashboard/login")
async def dashboard_login(request: Request, password: str = Form(...)):
    client_ip = request.client.host
    if _check_ip_blocked(client_ip):
        return HTMLResponse("<h1>Too many failed attempts. Try again in 1 minute.</h1>", status_code=429)
        
    if password == DASH_PASSWORD:
        _reset_attempts(client_ip)
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="dash_auth", value=password, max_age=86400 * 30, httponly=True)
        return response
        
    _record_failed_attempt(client_ip)
    
    state = AUTH_STATE.get(client_ip, {})
    attempts = state.get("attempts", 0)
    msg = "Invalid password."
    if attempts > 0:
        msg += f" ({3 - attempts} attempts remaining)"
        
    if _check_ip_blocked(client_ip):
        msg = "Too many failed attempts. Blocked for 1 minute."
        
    error_html = f"""
        <!DOCTYPE html>
        <html><head><title>Dashboard Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background: #0a0a0f; color: white; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            form {{ background: rgba(18, 18, 30, 0.65); padding: 40px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); text-align: center; width: 100%; max-width: 400px; box-sizing: border-box; }}
            h2 {{ margin-top: 0; }}
            input[type=password] {{ padding: 12px; border-radius: 8px; border: 1px solid #f43f5e; background: #1a1a24; color: white; width: 100%; box-sizing: border-box; margin-bottom: 20px; outline: none; }}
            button {{ background: linear-gradient(135deg, #a855f7, #6366f1); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; transition: 0.3s; }}
            button:hover {{ opacity: 0.9; transform: translateY(-1px); }}
            .error {{ color: #f43f5e; margin-bottom: 15px; font-size: 0.9em; background: rgba(244, 63, 94, 0.1); padding: 10px; border-radius: 6px; border: 1px solid rgba(244, 63, 94, 0.2); }}
        </style>
        </head><body>
        <form method="POST" action="/dashboard/login">
            <h2>Dashboard Access</h2>
            <div class="error">{msg}</div>
            <input type="password" name="password" placeholder="Password" required autofocus>
            <button type="submit">Unlock Dashboard</button>
        </form>
        </body></html>
    """
    return HTMLResponse(content=error_html)


# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    # Fallback: serve from frontend directory directly
    frontend_dev = Path(__file__).parent.parent / "frontend"
    if frontend_dev.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dev), html=True), name="frontend")
