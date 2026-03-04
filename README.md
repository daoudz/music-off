# 🎵 Music-Off: AI Music Remover

Remove music from audio and video files using AI, while preserving voice and sound effects.

🌐 **[اقرأ بالعربية](README_AR.md)**

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Demucs](https://img.shields.io/badge/AI-Demucs%20by%20Meta-purple)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)

## ✨ Features

- 🧠 **AI-Powered** — Uses Meta's Demucs model for state-of-the-art music source separation
- 🎬 **Video + Audio** — Supports MP4, MKV, AVI, MOV, MP3, WAV, FLAC, and more
- ⏱️ **Up to 10 minutes** — Process media files up to 10 minutes long
- 🎯 **Preserves Voice** — Removes only music while keeping dialogue and speech
- 📂 **Custom Output** — Browse or type a folder path to save results anywhere on your computer
- ⚡ **GPU Accelerated** — Automatically uses your GPU (NVIDIA CUDA) if available for faster processing
- 🖥️ **Beautiful UI** — Premium dark theme with drag-and-drop upload

---

## 🚀 Getting Started (Step-by-Step)

Follow these instructions carefully — no programming experience needed!

### Step 1: Install Python

1. Go to **[python.org/downloads](https://python.org/downloads)**
2. Click the big yellow **"Download Python"** button
3. Run the downloaded installer
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer before clicking "Install Now"
5. Click **"Install Now"** and wait for it to finish

> **How to verify:** Open the Start Menu, type `cmd`, press Enter, then type `python --version` and press Enter. You should see something like `Python 3.12.x`.

### Step 2: Install FFmpeg (Required for Video Files)

FFmpeg is needed to process video files (MP4, MKV, etc.). If you only plan to use audio files (MP3, WAV), you can skip this step.

1. Go to **[ffmpeg.org/download.html](https://ffmpeg.org/download.html)**
2. Under **"Get packages & executable files"**, click the **Windows** icon
3. Click on **"Windows builds from gyan.dev"**
4. Download the **ffmpeg-release-essentials.zip** file
5. Extract (unzip) the downloaded file to a folder, for example: `C:\ffmpeg`
6. **Add FFmpeg to your system PATH:**
   - Press `Win + R`, type `sysdm.cpl`, and press Enter
   - Go to the **"Advanced"** tab → Click **"Environment Variables"**
   - Under **"System variables"**, find and select **"Path"** → Click **"Edit"**
   - Click **"New"** and add the path to FFmpeg's `bin` folder, e.g.: `C:\ffmpeg\bin`
   - Click **OK** on all windows to save

> **How to verify:** Open a **new** Command Prompt window, type `ffmpeg -version` and press Enter. You should see version information.

### Step 3: Download Music-Off

**Option A — Download as ZIP (easiest):**
1. On this GitHub page, click the green **"Code"** button
2. Click **"Download ZIP"**
3. Extract the ZIP to a folder, for example: `C:\Users\YourName\music-off`

**Option B — Using Git (if you have Git installed):**
```
git clone https://github.com/daoudz/music-off.git
```

### Step 4: Run the Setup Script

1. Open the folder where you extracted/cloned Music-Off
2. **Double-click** the file called **`setup.bat`**
3. A command window will open and start installing everything automatically
4. Wait for it to finish — this may take **5–10 minutes** as it downloads the AI model and dependencies
5. When you see **"Setup complete!"**, press any key to close the window

### Step 5: Start the App

1. **Double-click** the file called **`start.py`**
   - If that doesn't work, open Command Prompt in the Music-Off folder and run:
     ```
     venv\Scripts\activate
     python start.py
     ```
2. Your web browser will automatically open to **http://127.0.0.1:8765**
3. The app is now running! 🎉

---

## 🎬 How to Use

1. **Set Output Folder** — Click the **📁 Browse** button (or type a path) to choose where your processed files will be saved
2. **Upload a File** — Drag & drop a file onto the upload area, or click to browse for a file
3. **Wait for AI Processing** — The AI will separate the audio into stems. This takes **1–5 minutes** depending on file length and your computer
4. **Download** — When done, click **Download** to save the music-free file, or find it in your chosen output folder

---

## 🔧 How It Works

1. **Upload** — You drag & drop or select an audio/video file
2. **Extract** — For video files, the audio track is extracted using FFmpeg
3. **AI Separation** — Meta's Demucs AI model separates the audio into 4 stems: vocals, drums, bass, and other instruments
4. **Keep Vocals** — Only the vocals stem is kept; all music stems (drums, bass, instruments) are discarded
5. **Output** — The vocals-only audio is saved as a WAV file, or remuxed back into the original video

---

## 📋 Supported Formats

| Type | Formats |
|------|---------|
| **Audio** | MP3, WAV, FLAC, OGG, AAC, M4A, WMA |
| **Video** | MP4, MKV, AVI, MOV, WebM, FLV, WMV |

**Limits:** Maximum file size is **500 MB** and maximum duration is **10 minutes**.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI Model | Demucs (htdemucs) by Meta |
| Backend | Python + FastAPI |
| Media Processing | FFmpeg |
| Frontend | Vanilla HTML / CSS / JS |

---

## ❓ Troubleshooting

### "Python is not recognized as a command"
You need to install Python and make sure you checked **"Add Python to PATH"** during installation. Reinstall Python if needed.

### "FFmpeg not found"
FFmpeg is not in your system PATH. Follow Step 2 above carefully. After adding it to PATH, you must **close and reopen** any Command Prompt or terminal windows.

### "AI separation failed"
- Make sure the setup script (`setup.bat`) completed without errors
- Try running the setup script again
- Check that you have at least **2 GB of free disk space** for the AI model

### The app is slow
- Processing speed depends on file length and your hardware
- A **1-minute file** typically takes **1–3 minutes** on CPU
- If you have an NVIDIA GPU, install [CUDA-enabled PyTorch](https://pytorch.org/get-started/locally/) for much faster processing

### Port 8765 is already in use
Another instance of Music-Off may be running. Close it first, or restart your computer.

---

## 📄 License

MIT
