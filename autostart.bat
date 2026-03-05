@echo off
REM Music-Off: Auto-start script (runs silently at Windows startup)
cd /d "c:\Users\daoud\projects\music-off"

REM Refresh PATH to pick up FFmpeg
set PATH=%PATH%;C:\Users\daoud\.ffmpeg\bin

REM Start the server
call venv\Scripts\python.exe start.py
