/**
 * Music-Off: Admin Dashboard
 * Real-time metrics polling and Chart.js visualization.
 */

const API = window.location.origin;
const POLL_MS = 3000;

// --- Chart.js setup ---
const chartColors = {
    purple: 'rgba(168, 85, 247, 1)',
    purpleFade: 'rgba(168, 85, 247, 0.15)',
    indigo: 'rgba(99, 102, 241, 1)',
    indigoFade: 'rgba(99, 102, 241, 0.15)',
    cyan: 'rgba(6, 182, 212, 1)',
    cyanFade: 'rgba(6, 182, 212, 0.15)',
    green: 'rgba(52, 211, 153, 1)',
    greenFade: 'rgba(52, 211, 153, 0.15)',
    red: 'rgba(244, 63, 94, 1)',
    redFade: 'rgba(244, 63, 94, 0.15)',
    gridColor: 'rgba(255,255,255,0.04)',
    tickColor: 'rgba(255,255,255,0.25)',
};

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: { color: chartColors.tickColor, font: { size: 11 } },
        },
    },
    scales: {
        x: {
            grid: { color: chartColors.gridColor },
            ticks: { color: chartColors.tickColor, font: { size: 10 } },
        },
        y: {
            grid: { color: chartColors.gridColor },
            ticks: { color: chartColors.tickColor, font: { size: 10 } },
            min: 0,
        },
    },
};

// System chart (CPU & RAM live line)
const MAX_SYSTEM_POINTS = 40;
const systemLabels = [];
const cpuData = [];
const ramData = [];

const systemChart = new Chart(document.getElementById('systemChart'), {
    type: 'line',
    data: {
        labels: systemLabels,
        datasets: [
            {
                label: 'CPU %',
                data: cpuData,
                borderColor: chartColors.purple,
                backgroundColor: chartColors.purpleFade,
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
            },
            {
                label: 'RAM %',
                data: ramData,
                borderColor: chartColors.cyan,
                backgroundColor: chartColors.cyanFade,
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
            },
        ],
    },
    options: {
        ...chartDefaults,
        scales: {
            ...chartDefaults.scales,
            y: { ...chartDefaults.scales.y, max: 100, ticks: { ...chartDefaults.scales.y.ticks, callback: v => v + '%' } },
        },
        animation: { duration: 300 },
    },
});

// History chart (bar: completed vs errors)
const historyChart = new Chart(document.getElementById('historyChart'), {
    type: 'bar',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Completed',
                data: [],
                backgroundColor: chartColors.greenFade,
                borderColor: chartColors.green,
                borderWidth: 1,
                borderRadius: 4,
            },
            {
                label: 'Errors',
                data: [],
                backgroundColor: chartColors.redFade,
                borderColor: chartColors.red,
                borderWidth: 1,
                borderRadius: 4,
            },
        ],
    },
    options: {
        ...chartDefaults,
        scales: {
            ...chartDefaults.scales,
            y: { ...chartDefaults.scales.y, ticks: { ...chartDefaults.scales.y.ticks, stepSize: 1 } },
        },
    },
});

// --- Helpers ---
function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m`;
}

function formatDuration(sec) {
    if (sec < 60) return `${sec}s`;
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return `${m}m ${s}s`;
}

function timeAgo(timestamp) {
    const diff = (Date.now() / 1000) - timestamp;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
}

// --- Update Functions ---
function updateKPIs(data) {
    // Processed
    document.getElementById('kpiProcessed').textContent = data.totals.processed;
    document.getElementById('kpiErrors').textContent = `${data.totals.errors} error${data.totals.errors !== 1 ? 's' : ''}`;

    // Queue
    document.getElementById('kpiQueue').textContent = data.queue.queued;
    document.getElementById('kpiActive').textContent = `${data.queue.active} active`;

    // CPU
    document.getElementById('kpiCPU').textContent = data.system.cpu_percent + '%';
    document.getElementById('kpiRAM').textContent =
        `${data.system.ram_used_gb} / ${data.system.ram_total_gb} GB RAM`;

    // Storage
    document.getElementById('kpiStorage').textContent = formatBytes(data.storage.total_bytes);
    document.getElementById('kpiStorageSub').textContent =
        `temp: ${formatBytes(data.storage.temp_dir_bytes)} · output: ${formatBytes(data.storage.output_dir_bytes)}`;

    // Bandwidth
    const totalBw = data.totals.bytes_uploaded + data.totals.bytes_downloaded;
    document.getElementById('kpiBandwidth').textContent = formatBytes(totalBw);
    document.getElementById('kpiBandwidthSub').textContent =
        `↑ ${formatBytes(data.totals.bytes_uploaded)} / ↓ ${formatBytes(data.totals.bytes_downloaded)}`;

    // Uptime
    document.getElementById('kpiUptime').textContent = formatUptime(data.uptime_seconds);
}

function updateSystemChart(data) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    systemLabels.push(now);
    cpuData.push(data.system.cpu_percent);
    ramData.push(data.system.ram_percent);

    if (systemLabels.length > MAX_SYSTEM_POINTS) {
        systemLabels.shift();
        cpuData.shift();
        ramData.shift();
    }

    systemChart.update('none');
}

function updateHistoryChart(data) {
    // Group history by hour
    const buckets = {};
    for (const entry of data.history) {
        const d = new Date(entry.timestamp * 1000);
        const key = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (!buckets[key]) buckets[key] = { completed: 0, errors: 0 };
        if (entry.status === 'completed') buckets[key].completed++;
        else buckets[key].errors++;
    }

    const keys = Object.keys(buckets).slice(-12);
    historyChart.data.labels = keys;
    historyChart.data.datasets[0].data = keys.map(k => buckets[k]?.completed || 0);
    historyChart.data.datasets[1].data = keys.map(k => buckets[k]?.errors || 0);
    historyChart.update('none');
}

function updateActiveJobs(data) {
    const tbody = document.getElementById('activeJobsBody');

    if (!data.active_jobs || data.active_jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No active jobs</td></tr>';
        return;
    }

    tbody.innerHTML = data.active_jobs.map(j => `
        <tr>
            <td style="font-family: monospace; font-size: 0.75rem;">${j.id}</td>
            <td>${escapeHtml(j.filename)}</td>
            <td><span class="status-badge status-${j.status}">${j.status}${j.queue_position > 0 ? ' #' + j.queue_position : ''}</span></td>
            <td>
                <span class="progress-mini"><span class="progress-mini-bar" style="width:${j.progress}%"></span></span>
                ${j.progress}%
            </td>
            <td>${formatDuration(j.elapsed)}</td>
        </tr>
    `).join('');
}

function updateHistory(data) {
    const tbody = document.getElementById('historyBody');

    if (!data.history || data.history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No processing history yet</td></tr>';
        return;
    }

    // Show most recent first
    const recent = [...data.history].reverse().slice(0, 20);
    tbody.innerHTML = recent.map(h => `
        <tr>
            <td>${timeAgo(h.timestamp)}</td>
            <td>${escapeHtml(h.filename)}</td>
            <td><span class="status-badge status-${h.status}">${h.status}</span></td>
            <td>${formatDuration(h.duration_sec)}</td>
            <td>${h.output_size > 0 ? formatBytes(h.output_size) : '—'}</td>
        </tr>
    `).join('');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// --- Polling ---
async function fetchMetrics() {
    try {
        const res = await fetch(`${API}/api/metrics`, { credentials: 'same-origin' });
        if (res.status === 401 || res.status === 429) {
            window.location.reload();
            return;
        }
        const data = await res.json();

        updateKPIs(data);
        updateSystemChart(data);
        updateHistoryChart(data);
        updateActiveJobs(data);
        updateHistory(data);
    } catch (err) {
        console.error('Metrics fetch failed:', err);
    }
}

// --- Init ---
fetchMetrics();
setInterval(fetchMetrics, POLL_MS);
