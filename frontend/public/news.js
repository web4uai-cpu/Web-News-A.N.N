/**
 * A.N.N. Public News Website — Application Logic
 * ═══════════════════════════════════════════════════
 * BBC/CNN-style live news interface connected to FastAPI backend.
 */

const API = window.location.origin;

/* ── State ──────────────────────────────────────────── */
const state = {
    scripts: [],
    filteredScripts: [],
    activeCategory: 'all',
    activeScript: null,
    readerLang: 'en',
    tickerItems: [],
};

/* ── Category Config ────────────────────────────────── */
const CATEGORIES = [
    { key: 'all', label: 'All News', icon: '📰' },
    { key: 'technology', label: 'Tech', icon: '💻' },
    { key: 'business', label: 'Business', icon: '💼' },
    { key: 'politics', label: 'Politics', icon: '🏛️' },
    { key: 'finance', label: 'Finance', icon: '📈' },
    { key: 'health', label: 'Health', icon: '🏥' },
    { key: 'science', label: 'Science', icon: '🔬' },
    { key: 'sports', label: 'Sports', icon: '⚽' },
    { key: 'entertainment', label: 'Entertainment', icon: '🎬' },
    { key: 'geopolitics', label: 'World', icon: '🌍' },
];

const CAT_COLORS = {
    technology: '#3b82f6', business: '#10b981', politics: '#f59e0b',
    finance: '#22d3ee', health: '#ec4899', science: '#a78bfa',
    sports: '#f97316', entertainment: '#e879f9', geopolitics: '#ef4444',
    general: '#6b7280',
};

/* ── Init ───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    renderCategories();
    updateClock();
    setInterval(updateClock, 1000);
    fetchScripts();
    setInterval(fetchScripts, 30000); // Auto-refresh every 30s

    // Close reader on overlay click
    document.getElementById('reader-overlay')?.addEventListener('click', (e) => {
        if (e.target.id === 'reader-overlay') closeReader();
    });

    // Close on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeReader();
    });
});

/* ── Fetch Scripts from Backend ─────────────────────── */
async function fetchScripts() {
    try {
        const res = await fetch(`${API}/api/v1/scripts?limit=50`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        state.scripts = data;
        applyFilter();
        updateTicker();
        updateHero();
    } catch (err) {
        console.warn('Failed to fetch scripts:', err.message);
        // Show demo content if API has no scripts
        if (state.scripts.length === 0) {
            showEmptyState();
        }
    }
}

/* ── Category Navigation ────────────────────────────── */
function renderCategories() {
    const nav = document.getElementById('nav-categories');
    if (!nav) return;

    nav.innerHTML = CATEGORIES.map(cat => `
        <button class="nav-cat ${cat.key === state.activeCategory ? 'active' : ''}"
                onclick="filterCategory('${cat.key}')"
                id="cat-${cat.key}">
            ${cat.label}
        </button>
    `).join('');
}

function filterCategory(category) {
    state.activeCategory = category;
    // Update active state
    document.querySelectorAll('.nav-cat').forEach(btn => {
        btn.classList.toggle('active', btn.id === `cat-${category}`);
    });
    applyFilter();
}

function applyFilter() {
    if (state.activeCategory === 'all') {
        state.filteredScripts = [...state.scripts];
    } else {
        state.filteredScripts = state.scripts.filter(
            s => s.category === state.activeCategory
        );
    }
    renderNewsFeed();
}

/* ── Breaking News Ticker ───────────────────────────── */
function updateTicker() {
    const track = document.getElementById('ticker-content');
    if (!track) return;

    const headlines = state.scripts.length > 0
        ? state.scripts.slice(0, 15).map(s => s.headline)
        : [
            'A.N.N. — AI News Network is now live',
            'Autonomous AI-powered news broadcasting system operational',
            'Run the pipeline from the admin dashboard to generate news',
            'Multi-lingual broadcasts in English and Hindi',
        ];

    // Duplicate for seamless loop
    const items = [...headlines, ...headlines].map((h, i) =>
        `<span class="ticker-item" onclick="openScriptByHeadline('${escapeAttr(h)}')">${esc(h)}</span>
         <span class="ticker-separator">◆</span>`
    ).join('');

    track.innerHTML = items;

    // Adjust speed based on content width
    const duration = Math.max(30, headlines.length * 6);
    track.style.setProperty('--ticker-duration', `${duration}s`);
    track.parentElement.style.setProperty('--ticker-duration', `${duration}s`);
}

/* ── Hero Section ───────────────────────────────────── */
function updateHero() {
    const featured = state.scripts[0];
    const heroHeadline = document.getElementById('hero-headline');
    const heroExcerpt = document.getElementById('hero-excerpt');
    const heroCat = document.getElementById('hero-category');
    const heroTime = document.getElementById('hero-time');
    const heroDuration = document.getElementById('hero-duration');

    if (!featured) {
        if (heroHeadline) heroHeadline.textContent = 'A.N.N. — AI News Network';
        if (heroExcerpt) heroExcerpt.textContent = 'Your autonomous AI-powered news broadcast system is online. Use the admin dashboard to ingest news sources and generate broadcast scripts.';
        return;
    }

    if (heroHeadline) heroHeadline.textContent = featured.headline;
    if (heroExcerpt) heroExcerpt.textContent = featured.english_script.replace(/\[PAUSE\]/g, '').substring(0, 250) + '...';
    if (heroCat) {
        heroCat.textContent = featured.category;
        heroCat.className = `hero-meta-cat cat-bg-${featured.category}`;
    }
    if (heroTime) heroTime.textContent = timeAgo(featured.created_at);
    if (heroDuration) heroDuration.textContent = `~${featured.estimated_duration_seconds}s`;

    // Update hero click handler
    const heroMain = document.getElementById('hero-main');
    if (heroMain) {
        heroMain.onclick = () => openReader(featured);
    }

    // Update sidebar
    updateSidebar();
}

function updateSidebar() {
    const sidebar = document.getElementById('hero-sidebar-stories');
    if (!sidebar) return;

    const stories = state.scripts.slice(1, 7);
    if (stories.length === 0) {
        sidebar.innerHTML = `
            <div class="sidebar-story">
                <div class="sidebar-story-cat cat-general">System</div>
                <div class="sidebar-story-title">Waiting for news scripts...</div>
                <div class="sidebar-story-time">Run pipeline from dashboard</div>
            </div>
        `;
        return;
    }

    sidebar.innerHTML = stories.map(s => `
        <div class="sidebar-story" onclick='openReader(${JSON.stringify(s).replace(/'/g, "&#39;")})'>
            <div class="sidebar-story-cat cat-${s.category}">${s.category.toUpperCase()}</div>
            <div class="sidebar-story-title">${esc(s.headline)}</div>
            <div class="sidebar-story-time">${timeAgo(s.created_at)}</div>
        </div>
    `).join('');
}

/* ── News Feed Grid ─────────────────────────────────── */
function renderNewsFeed() {
    const grid = document.getElementById('news-grid');
    if (!grid) return;

    if (state.filteredScripts.length === 0) {
        showEmptyState();
        return;
    }

    grid.innerHTML = state.filteredScripts.map((s, i) => `
        <article class="news-card" onclick='openReader(${JSON.stringify(s).replace(/'/g, "&#39;")})'>
            <div class="news-card-cat-strip cat-bg-${s.category}"></div>
            <div class="news-card-body">
                <div class="news-card-category cat-${s.category}">${s.category}</div>
                <h3 class="news-card-headline">${esc(s.headline)}</h3>
                <p class="news-card-excerpt">${esc(s.english_script.replace(/\[PAUSE\]/g, '').substring(0, 200))}</p>
            </div>
            <div class="news-card-footer">
                <div class="news-card-meta">
                    <span>📝 ${s.word_count_en} words</span>
                    <span>⏱ ~${s.estimated_duration_seconds}s</span>
                    <span>${timeAgo(s.created_at)}</span>
                </div>
                <div class="news-card-lang-toggle" onclick="event.stopPropagation()">
                    <button class="lang-btn active" onclick="toggleCardLang(this, '${s.id}', 'en')">EN</button>
                    <button class="lang-btn" onclick="toggleCardLang(this, '${s.id}', 'hi')">HI</button>
                </div>
            </div>
        </article>
    `).join('');
}

function showEmptyState() {
    const grid = document.getElementById('news-grid');
    if (!grid) return;
    grid.innerHTML = `
        <div class="empty-feed">
            <div class="empty-feed-icon">📡</div>
            <h3 class="empty-feed-title">No Broadcasts Available</h3>
            <p class="empty-feed-desc">
                The AI newsroom is standing by. Go to the 
                <a href="/" style="color: var(--accent-secondary);">Admin Dashboard</a> 
                to run the pipeline and generate broadcast scripts.
            </p>
            <a href="/" class="btn btn-red">🎛️ Open Dashboard</a>
        </div>
    `;
}

function toggleCardLang(btn, scriptId, lang) {
    const card = btn.closest('.news-card');
    if (!card) return;
    const script = state.scripts.find(s => s.id === scriptId);
    if (!script) return;

    // Update button states
    card.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Update excerpt text
    const excerpt = card.querySelector('.news-card-excerpt');
    if (excerpt) {
        const text = lang === 'hi' ? script.hindi_script : script.english_script;
        excerpt.textContent = text.replace(/\[PAUSE\]/g, '').substring(0, 200);
    }
}

/* ── Script Reader Modal ────────────────────────────── */
function openReader(script) {
    state.activeScript = script;
    state.readerLang = 'en';

    const overlay = document.getElementById('reader-overlay');
    const headline = document.getElementById('reader-headline');
    const category = document.getElementById('reader-category');
    const metaWords = document.getElementById('reader-words');
    const metaDuration = document.getElementById('reader-duration');
    const metaTime = document.getElementById('reader-time');
    const scriptText = document.getElementById('reader-script-text');

    if (headline) headline.textContent = script.headline;
    if (category) {
        category.textContent = script.category;
        category.className = `reader-category cat-${script.category}`;
    }
    if (metaWords) metaWords.textContent = `${script.word_count_en} words`;
    if (metaDuration) metaDuration.textContent = `~${script.estimated_duration_seconds}s`;
    if (metaTime) metaTime.textContent = timeAgo(script.created_at);
    if (scriptText) scriptText.innerHTML = formatScript(script.english_script);

    // Reset lang tabs
    document.querySelectorAll('.reader-lang-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.reader-lang-tab[data-lang="en"]')?.classList.add('active');

    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeReader() {
    const overlay = document.getElementById('reader-overlay');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
    state.activeScript = null;
}

function switchReaderLang(btn, lang) {
    if (!state.activeScript) return;
    state.readerLang = lang;

    document.querySelectorAll('.reader-lang-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');

    const scriptText = document.getElementById('reader-script-text');
    const metaWords = document.getElementById('reader-words');

    const text = lang === 'hi' ? state.activeScript.hindi_script : state.activeScript.english_script;
    const wordCount = lang === 'hi' ? state.activeScript.word_count_hi : state.activeScript.word_count_en;

    if (scriptText) scriptText.innerHTML = formatScript(text);
    if (metaWords) metaWords.textContent = `${wordCount} words`;
}

function copyReaderScript() {
    if (!state.activeScript) return;
    const text = state.readerLang === 'hi'
        ? state.activeScript.hindi_script
        : state.activeScript.english_script;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById('copy-btn');
        if (btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = '✅ Copied!';
            setTimeout(() => btn.innerHTML = orig, 2000);
        }
    });
}

function openScriptByHeadline(headline) {
    const script = state.scripts.find(s => s.headline === headline);
    if (script) openReader(script);
}

/* ── Format Script Text ─────────────────────────────── */
function formatScript(text) {
    if (!text) return '';
    return esc(text)
        .replace(/\[PAUSE\]/g, '<span class="pause-marker">PAUSE</span>')
        .replace(/\n/g, '<br>');
}

/* ── Clock ──────────────────────────────────────────── */
function updateClock() {
    const el = document.getElementById('nav-clock');
    if (!el) return;
    const now = new Date();
    const opts = {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false,
    };
    el.textContent = now.toLocaleDateString('en-US', opts);
}

/* ── Utilities ──────────────────────────────────────── */
function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function esc(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function escapeAttr(text) {
    if (!text) return '';
    return text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
