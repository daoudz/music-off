/**
 * Music-Off: Frontend Application Logic
 * Handles file upload, processing status, and result display.
 */

const API_BASE = window.location.origin;

// --- DOM Elements ---
const uploadSection = document.getElementById('uploadSection');
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const processingSection = document.getElementById('processingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const waveformContainer = document.getElementById('waveformContainer');

// File info
const fileName = document.getElementById('fileName');
const fileDetails = document.getElementById('fileDetails');
const fileTypeIcon = document.getElementById('fileTypeIcon');

// Progress
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const progressPercent = document.getElementById('progressPercent');
const statusMessage = document.getElementById('statusMessage');

// Result
const resultFilename = document.getElementById('resultFilename');
const resultPath = document.getElementById('resultPath');
const downloadBtn = document.getElementById('downloadBtn');
const newFileBtn = document.getElementById('newFileBtn');

// Error
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const cancelBtn = document.getElementById('cancelBtn');

// Output dir
const outputDir = document.getElementById('outputDir');
const setOutputBtn = document.getElementById('setOutputBtn');
const browseOutputBtn = document.getElementById('browseOutputBtn');
const outputStatus = document.getElementById('outputStatus');

// Device info
const deviceText = document.getElementById('deviceText');

// --- State ---
let currentJobId = null;
let pollInterval = null;

// --- Supported formats ---
const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma'];
const VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'];
const ALL_EXTENSIONS = [...AUDIO_EXTENSIONS, ...VIDEO_EXTENSIONS];

// --- Initialize ---
async function init() {
    await checkHealth();
    await loadOutputDir();
    setupEventListeners();
}

// --- Health Check ---
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();

        deviceText.textContent = data.device || 'CPU';
        document.querySelector('.device-dot').style.background =
            data.cuda ? '#34d399' : '#f59e0b';

        if (!data.ffmpeg) {
            showOutputStatus('⚠ FFmpeg not found — video processing will not work. Install from ffmpeg.org', 'error');
        }
    } catch {
        deviceText.textContent = 'Server offline';
        document.querySelector('.device-dot').style.background = '#f43f5e';
    }
}

// --- Output Directory ---
async function loadOutputDir() {
    try {
        const res = await fetch(`${API_BASE}/api/output-dir`);
        const data = await res.json();
        if (data.path) {
            outputDir.value = data.path;
        }
    } catch { /* ignore */ }
}

async function setOutputDirectory() {
    const dir = outputDir.value.trim();
    if (!dir) {
        showOutputStatus('Please enter a directory path', 'error');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('directory', dir);

        const res = await fetch(`${API_BASE}/api/set-output-dir`, {
            method: 'POST',
            body: formData,
        });

        const data = await res.json();

        if (res.ok) {
            showOutputStatus(`✅ Output set to: ${data.path}`, 'success');
        } else {
            showOutputStatus(`❌ ${data.detail}`, 'error');
        }
    } catch {
        showOutputStatus('❌ Failed to connect to server', 'error');
    }
}

async function browseForFolder() {
    browseOutputBtn.disabled = true;
    browseOutputBtn.textContent = '⏳ Opening...';

    try {
        const res = await fetch(`${API_BASE}/api/browse-folder`);
        const data = await res.json();

        if (data.selected && data.path) {
            outputDir.value = data.path;
            showOutputStatus(`✅ Output set to: ${data.path}`, 'success');
        }
    } catch {
        showOutputStatus('❌ Failed to open folder picker', 'error');
    } finally {
        browseOutputBtn.disabled = false;
        browseOutputBtn.textContent = '📁 Browse';
    }
}

function showOutputStatus(msg, type) {
    outputStatus.textContent = msg;
    outputStatus.className = `output-status ${type}`;
    setTimeout(() => {
        outputStatus.textContent = '';
        outputStatus.className = 'output-status';
    }, 5000);
}

// --- Event Listeners ---
function setupEventListeners() {
    // Click to upload
    uploadZone.addEventListener('click', () => fileInput.click());

    // File selected
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Buttons
    setOutputBtn.addEventListener('click', setOutputDirectory);
    browseOutputBtn.addEventListener('click', browseForFolder);
    cancelBtn.addEventListener('click', resetToUpload);
    newFileBtn.addEventListener('click', resetToUpload);
    retryBtn.addEventListener('click', resetToUpload);

    downloadBtn.addEventListener('click', () => {
        if (currentJobId) {
            window.open(`${API_BASE}/api/download/${currentJobId}`, '_blank');
        }
    });

    // Enter key on output dir input
    outputDir.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') setOutputDirectory();
    });
}

// --- File Handling ---
function handleFile(file) {
    // Validate extension
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALL_EXTENSIONS.includes(ext)) {
        showError(`Unsupported format "${ext}". Supported: ${ALL_EXTENSIONS.join(', ')}`);
        return;
    }

    // Validate size (500MB)
    if (file.size > 500 * 1024 * 1024) {
        showError('File is too large. Maximum size is 500MB.');
        return;
    }

    // Show file info
    const isVideo = VIDEO_EXTENSIONS.includes(ext);
    fileTypeIcon.textContent = isVideo ? '🎬' : '🎵';
    fileName.textContent = file.name;
    fileDetails.textContent = formatFileSize(file.size);

    // Upload
    uploadFile(file);
}

async function uploadFile(file) {
    showSection('processing');
    updateProgress(0, 'Uploading file...');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData,
        });

        const data = await res.json();

        if (!res.ok) {
            showError(data.detail || 'Upload failed');
            return;
        }

        currentJobId = data.job_id;
        updateProgress(5, 'File uploaded, starting AI processing...');
        startPolling();
    } catch (err) {
        showError(`Upload failed: ${err.message}. Is the server running?`);
    }
}

// --- Status Polling ---
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        if (!currentJobId) return;

        try {
            const res = await fetch(`${API_BASE}/api/status/${currentJobId}`);
            const job = await res.json();

            if (job.status === 'processing' || job.status === 'queued') {
                updateProgress(job.progress, job.message);
            } else if (job.status === 'completed') {
                stopPolling();
                showResult(job);
            } else if (job.status === 'error') {
                stopPolling();
                showError(job.message);
            }
        } catch {
            // Retry on network error
        }
    }, 1000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// --- UI Updates ---
function updateProgress(percent, message) {
    progressBar.style.width = `${percent}%`;
    progressPercent.textContent = `${percent}%`;
    if (message) {
        progressText.textContent = message;
        statusMessage.textContent = message;
    }
}

function showSection(section) {
    uploadSection.classList.add('hidden');
    processingSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    switch (section) {
        case 'upload':
            uploadSection.classList.remove('hidden');
            break;
        case 'processing':
            processingSection.classList.remove('hidden');
            break;
        case 'result':
            resultSection.classList.remove('hidden');
            break;
        case 'error':
            errorSection.classList.remove('hidden');
            break;
    }
}

function showResult(job) {
    resultFilename.textContent = job.output_filename || 'processed file';
    resultPath.textContent = job.output_file
        ? `Saved to: ${job.output_file}`
        : 'Available for download';
    showSection('result');
}

function showError(message) {
    stopPolling();
    waveformContainer.classList.add('paused');
    errorMessage.textContent = message;
    showSection('error');
}

function resetToUpload() {
    stopPolling();
    currentJobId = null;
    fileInput.value = '';
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    waveformContainer.classList.remove('paused');
    showSection('upload');
}

// --- Utilities ---
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// --- Start ---
document.addEventListener('DOMContentLoaded', init);
