@echo off
echo ============================================
echo   Music-Off: Setup Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Download from: https://python.org/downloads
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found in PATH.
    echo Download from: https://ffmpeg.org/download.html
    echo Music-Off requires FFmpeg for video processing.
    echo.
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install core dependencies first
echo Installing core dependencies...
pip install -r requirements.txt

REM Install demucs without deps (to avoid lameenc issue on Python 3.14)
echo Installing Demucs AI model...
pip install --no-deps demucs==4.0.1

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo To start Music-Off, run:
echo   venv\Scripts\activate.bat
echo   python start.py
echo.
pause
