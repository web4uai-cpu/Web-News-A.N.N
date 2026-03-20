/**
 * A.N.N. (AI News Network) — Dashboard Application
 * ═══════════════════════════════════════════════════
 * Real-time control panel for the AI News Network.
 */

const API_BASE = window.location.origin;

// ── State ─────────────────────────────────────────────
const state = {
    scripts: [],
    activeJob: null,
    logs: [],
    stats: {
        scriptsGenerated: 0,
        articlesProcessed: 0,
        activeJobs: 0,
        uptime: '0s',
    },
};

// ── DOM References ────────────────────────────────────
const dom = {
    scriptsContainer: null,
    logBody: null,
    statsScripts: null,
    statsArticles: null,
    statsJobs: null,
    statsUptime: null,
    pipelineSteps: null,
    progressBar: null,
    toastContainer: null,
};

// ── Initialize ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    cacheDom();
    checkHealth();
    loadScripts();

    // Poll for updates every 5 seconds
    setInterval(checkHealth, 5000);
    setInterval(checkActiveJob, 3000);

    addLog('info', 'A.N.N. Dashboard initialized');
    addLog('ok', 'Systems online — awaiting commands');
});

function cacheDom() {
    dom.scriptsContainer = document.getElementById('scripts-container');
    dom.logBody = document.getElementById('log-body');
    dom.statsScripts = document.getElementById('stat-scripts');
    dom.statsArticles = document.getElementById('stat-articles');
    dom.statsJobs = document.getElementById('stat-jobs');
    dom.statsUptime = document.getElementById('stat-uptime');
    dom.pipelineSteps = document.getElementById('pipeline-steps');
    dom.progressBar = document.getElementById('progress-bar');
    dom.toastContainer = document.getElementById('toast-container');
}

// ── API Calls ─────────────────────────────────────────

async function apiCall(endpoint, method = 'GET', body = null) {
    try {
        const opts = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);

        const response = await fetch(`${API_BASE}${endpoint}`, opts);

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        addLog('error', `API Error: ${error.message}`);
        throw error;
    }
}

async function checkHealth() {
    try {
        const data = await apiCall('/health');
        state.stats.uptime = formatUptime(data.uptime_seconds);
        state.stats.activeJobs = data.active_jobs;

        if (dom.statsUptime) dom.statsUptime.textContent = state.stats.uptime;
        if (dom.statsJobs) dom.statsJobs.textContent = data.active_jobs;

        updateStatusBadge(true);
    } catch {
        updateStatusBadge(false);
    }
}

async function loadScripts() {
    try {
        const scripts = await apiCall('/api/v1/scripts?limit=20');
        state.scripts = scripts;
        state.stats.scriptsGenerated = scripts.length;

        if (dom.statsScripts) dom.statsScripts.textContent = scripts.length;
        renderScripts();
    } catch (e) {
        // API may not be running yet
    }
}

// ── Pipeline Control ──────────────────────────────────

async function runPipeline() {
    const source = document.getElementById('source-select')?.value || 'newsapi';
    const category = document.getElementById('category-select')?.value || 'general';
    const query = document.getElementById('query-input')?.value || '';
    const maxArticles = parseInt(document.getElementById('max-articles')?.value || '5');
    const generateMedia = document.getElementById('generate-media')?.checked || false;

    const runBtn = document.getElementById('run-pipeline-btn');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '<span class="spinner"></span> Running...';
    }

    addLog('info', `Starting pipeline: source=${source}, category=${category}`);
    showToast('Pipeline started...', 'info');

    try {
        const params = new URLSearchParams({
            generate_media: generateMedia,
            source: source,
        });

        const result = await apiCall(
            `/api/v1/pipeline/run?${params}`,
            'POST',
            {
                category,
                query: query || null,
                max_articles: maxArticles,
            }
        );

        state.activeJob = result.job_id;
        addLog('ok', `Pipeline job created: ${result.job_id}`);
        showToast(`Job ${result.job_id.slice(0, 8)}... started`, 'success');

        updatePipelineSteps('ingesting');

    } catch (error) {
        showToast(`Pipeline failed: ${error.message}`, 'error');
        addLog('error', `Pipeline failed: ${error.message}`);
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '🚀 Run Pipeline';
        }
    }
}

async function processManualArticle() {
    const urlInput = document.getElementById('manual-url');
    const textInput = document.getElementById('manual-text');

    if (!textInput?.value || textInput.value.length < 50) {
        showToast('Article text must be at least 50 characters', 'warning');
        return;
    }

    addLog('info', 'Processing manual article...');

    try {
        const script = await apiCall('/api/v1/process_news', 'POST', {
            source_url: urlInput?.value || 'manual-input',
            raw_text: textInput.value,
            source_name: 'Manual Input',
            category: 'general',
        });

        state.scripts.unshift(script);
        state.stats.scriptsGenerated++;
        if (dom.statsScripts) dom.statsScripts.textContent = state.stats.scriptsGenerated;

        renderScripts();
        showToast(`Script generated: "${script.headline}"`, 'success');
        addLog('ok', `Script created: ${script.id} — ${script.headline}`);

        // Clear inputs
        if (textInput) textInput.value = '';
        if (urlInput) urlInput.value = '';

    } catch (error) {
        showToast(`Processing failed: ${error.message}`, 'error');
    }
}

async function checkActiveJob() {
    if (!state.activeJob) return;

    try {
        const job = await apiCall(`/api/v1/pipeline/status/${state.activeJob}`);

        // Update progress
        if (dom.progressBar) {
            dom.progressBar.style.width = `${job.progress_pct}%`;
        }

        // Update pipeline steps
        updatePipelineSteps(job.status);

        // Log progress
        if (job.progress_pct > 0 && job.progress_pct < 100) {
            addLog('info', `Pipeline: ${job.status} (${job.progress_pct}%)`);
        }

        // Check completion
        if (job.status === 'completed') {
            state.activeJob = null;
            addLog('ok', `Pipeline complete! ${job.scripts?.length || 0} scripts generated`);
            showToast(`Pipeline complete! ${job.scripts?.length || 0} scripts ready.`, 'success');
            loadScripts();
            resetPipelineSteps();
        } else if (job.status === 'failed') {
            state.activeJob = null;
            const errorMsg = job.errors?.join(', ') || 'Unknown error';
            addLog('error', `Pipeline failed: ${errorMsg}`);
            showToast('Pipeline failed', 'error');
            resetPipelineSteps();
        }

    } catch (e) {
        // Job may have been cleaned up
    }
}

// ── Rendering ─────────────────────────────────────────

function renderScripts() {
    if (!dom.scriptsContainer) return;

    if (state.scripts.length === 0) {
        dom.scriptsContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📡</div>
                <div class="empty-state-title">No Scripts Yet</div>
                <div class="empty-state-desc">
                    Run the pipeline or process a manual article to generate your first broadcast script.
                </div>
            </div>
        `;
        return;
    }

    dom.scriptsContainer.innerHTML = state.scripts.map((script, idx) => `
        <div class="script-card fade-in-up" style="animation-delay: ${idx * 0.05}s">
            <div class="script-card-header">
                <span class="script-headline">${escapeHtml(script.headline)}</span>
                <span class="script-category">${script.category}</span>
            </div>
            <div class="script-body">
                <div class="script-tabs">
                    <button class="script-tab active" onclick="showScriptTab(this, '${script.id}', 'en')">
                        🇬🇧 English
                    </button>
                    <button class="script-tab" onclick="showScriptTab(this, '${script.id}', 'hi')">
                        🇮🇳 Hindi
                    </button>
                </div>
                <div class="script-text" id="script-text-${script.id}">
                    ${escapeHtml(script.english_script)}
                </div>
            </div>
            <div class="script-footer">
                <div class="script-meta">
                    <span class="script-meta-item">📝 ${script.word_count_en} words</span>
                    <span class="script-meta-item">⏱️ ~${script.estimated_duration_seconds}s</span>
                    <span class="script-meta-item">🆔 ${script.id}</span>
                </div>
                <div class="script-actions">
                    <button class="btn btn-secondary btn-sm" onclick="copyScript('${script.id}')">
                        📋 Copy
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="generateAudio('${script.id}')">
                        🎙️ Audio
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function showScriptTab(btn, scriptId, lang) {
    // Toggle tab style
    const tabs = btn.parentElement.querySelectorAll('.script-tab');
    tabs.forEach(t => t.classList.remove('active'));
    btn.classList.add('active');

    // Switch content
    const textEl = document.getElementById(`script-text-${scriptId}`);
    const script = state.scripts.find(s => s.id === scriptId);
    if (textEl && script) {
        textEl.textContent = lang === 'hi' ? script.hindi_script : script.english_script;
    }
}

function copyScript(scriptId) {
    const script = state.scripts.find(s => s.id === scriptId);
    if (script) {
        navigator.clipboard.writeText(script.english_script).then(() => {
            showToast('Script copied to clipboard!', 'success');
        });
    }
}

async function generateAudio(scriptId) {
    showToast('Audio generation started...', 'info');
    addLog('info', `Generating audio for script ${scriptId}`);
    try {
        const result = await apiCall('/api/v1/media/generate_audio', 'POST', {
            script_id: scriptId,
            language: 'en',
        });
        if (result.status === 'completed') {
            showToast('Audio generated successfully!', 'success');
            addLog('ok', `Audio ready: ${result.audio_url}`);
        } else {
            showToast(`Audio status: ${result.status}`, 'info');
            addLog('warn', `Audio status: ${result.status}`);
        }
    } catch (error) {
        showToast(`Audio failed: ${error.message}`, 'error');
    }
}

// ── Pipeline Steps ────────────────────────────────────

const PIPELINE_STEP_ORDER = [
    'queued', 'ingesting', 'extracting_facts',
    'writing_script', 'translating',
    'generating_audio', 'generating_video', 'completed'
];

const PIPELINE_STEP_LABELS = {
    queued: '📋 Queue',
    ingesting: '📡 Ingest',
    extracting_facts: '🔍 Extract',
    writing_script: '✍️ Script',
    translating: '🌐 Translate',
    generating_audio: '🎙️ Audio',
    generating_video: '🎬 Video',
    completed: '✅ Done',
};

function updatePipelineSteps(currentStatus) {
    if (!dom.pipelineSteps) return;

    const currentIdx = PIPELINE_STEP_ORDER.indexOf(currentStatus);

    dom.pipelineSteps.innerHTML = PIPELINE_STEP_ORDER.map((step, idx) => {
        let cls = 'pipeline-step';
        if (idx < currentIdx) cls += ' completed';
        else if (idx === currentIdx) cls += ' active';

        const arrow = idx < PIPELINE_STEP_ORDER.length - 1
            ? '<span class="pipeline-arrow">→</span>'
            : '';

        return `<span class="${cls}">${PIPELINE_STEP_LABELS[step]}</span>${arrow}`;
    }).join('');
}

function resetPipelineSteps() {
    if (dom.pipelineSteps) {
        dom.pipelineSteps.innerHTML = PIPELINE_STEP_ORDER.map(step =>
            `<span class="pipeline-step">${PIPELINE_STEP_LABELS[step]}</span>`
        ).join('<span class="pipeline-arrow">→</span>');
    }
    if (dom.progressBar) {
        dom.progressBar.style.width = '0%';
    }
}

// ── Logging ───────────────────────────────────────────

function addLog(level, message) {
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour12: false });

    const entry = { time, level, message };
    state.logs.unshift(entry);

    // Keep max 100 logs
    if (state.logs.length > 100) state.logs.pop();

    if (dom.logBody) {
        const el = document.createElement('div');
        el.className = 'log-entry';
        el.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-level ${level}">${level.toUpperCase()}</span>
            <span class="log-msg">${escapeHtml(message)}</span>
        `;
        dom.logBody.prepend(el);

        // Trim old entries from DOM
        while (dom.logBody.children.length > 100) {
            dom.logBody.removeChild(dom.logBody.lastChild);
        }
    }
}

// ── Toast Notifications ───────────────────────────────

function showToast(message, type = 'info') {
    if (!dom.toastContainer) return;

    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️',
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || ''}</span> ${escapeHtml(message)}`;

    dom.toastContainer.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        toast.style.transition = 'all 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Status Badge ──────────────────────────────────────

function updateStatusBadge(online) {
    const dot = document.getElementById('api-status-dot');
    const text = document.getElementById('api-status-text');
    if (dot) dot.style.background = online ? 'var(--status-success)' : 'var(--status-error)';
    if (text) text.textContent = online ? 'API Online' : 'API Offline';
}

// ── Utilities ─────────────────────────────────────────

function formatUptime(seconds) {
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
}

function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}
