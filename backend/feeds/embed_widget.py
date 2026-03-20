"""
A.N.N. Embeddable Widget Generator
Creates JavaScript embed widgets that other websites can drop in.
"""


def generate_ticker_widget_js(base_url: str = "http://localhost:8000") -> str:
    """
    Generate a self-contained JavaScript ticker widget.
    
    Other websites embed this via:
      <script src="http://your-server/embed/ticker.js"></script>
      <div id="ann-ticker"></div>
    """
    return f"""
(function() {{
  'use strict';
  const ANN_API = '{base_url}';
  const STYLE = `
    .ann-ticker-wrap {{
      background: #1a1a2e; overflow: hidden; height: 36px;
      display: flex; align-items: center; font-family: -apple-system, sans-serif;
      border-radius: 4px; position: relative;
    }}
    .ann-ticker-label {{
      background: #e53e3e; color: #fff; font-size: 11px; font-weight: 800;
      padding: 0 14px; height: 100%; display: flex; align-items: center;
      letter-spacing: 0.08em; text-transform: uppercase; flex-shrink: 0; z-index: 2;
    }}
    .ann-ticker-track {{
      flex: 1; overflow: hidden; height: 100%; display: flex; align-items: center;
      mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent);
      -webkit-mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent);
    }}
    .ann-ticker-scroll {{
      display: flex; white-space: nowrap;
      animation: annTickerMove var(--ann-dur, 45s) linear infinite;
    }}
    .ann-ticker-scroll:hover {{ animation-play-state: paused; }}
    .ann-ticker-item {{
      padding: 0 20px; font-size: 13px; font-weight: 600; color: #e0e0f0;
      cursor: pointer; text-decoration: none;
    }}
    .ann-ticker-item:hover {{ text-decoration: underline; }}
    .ann-ticker-sep {{ color: rgba(255,255,255,0.25); font-size: 8px; padding: 0 6px; }}
    @keyframes annTickerMove {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-50%); }} }}
  `;

  function init() {{
    var el = document.getElementById('ann-ticker');
    if (!el) return;

    // Inject styles
    var s = document.createElement('style');
    s.textContent = STYLE;
    document.head.appendChild(s);

    el.innerHTML = '<div class="ann-ticker-wrap"><div class="ann-ticker-label">⚡ A.N.N.</div><div class="ann-ticker-track"><div class="ann-ticker-scroll" id="ann-ticker-scroll">Loading...</div></div></div>';

    fetch(ANN_API + '/api/v1/scripts?limit=15')
      .then(function(r) {{ return r.json(); }})
      .then(function(scripts) {{
        var items = scripts.map(function(s) {{
          return '<a class="ann-ticker-item" href="' + ANN_API + '/news" target="_blank">' + esc(s.headline) + '</a><span class="ann-ticker-sep">◆</span>';
        }}).join('');
        if (!items) items = '<span class="ann-ticker-item">A.N.N. — AI News Network</span>';
        var scroll = document.getElementById('ann-ticker-scroll');
        scroll.innerHTML = items + items;
        scroll.style.setProperty('--ann-dur', Math.max(30, scripts.length * 5) + 's');
      }})
      .catch(function() {{
        document.getElementById('ann-ticker-scroll').innerHTML = '<span class="ann-ticker-item">A.N.N. — AI News Network Feed</span>';
      }});
  }}

  function esc(t) {{
    var d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init);
  }} else {{
    init();
  }}
}})();
"""


def generate_feed_widget_js(base_url: str = "http://localhost:8000") -> str:
    """
    Generate a self-contained news feed card widget.
    
    Other websites embed this via:
      <script src="http://your-server/embed/feed.js"></script>
      <div id="ann-feed"></div>
    """
    return f"""
(function() {{
  'use strict';
  const ANN_API = '{base_url}';
  const STYLE = `
    .ann-feed {{ font-family: -apple-system, sans-serif; max-width: 400px; }}
    .ann-feed-header {{
      background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;
      padding: 12px 16px; border-radius: 8px 8px 0 0; font-weight: 700;
      font-size: 14px; display: flex; align-items: center; gap: 8px;
    }}
    .ann-feed-list {{ background: #12121e; border-radius: 0 0 8px 8px; }}
    .ann-feed-item {{
      padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.06);
      cursor: pointer; transition: background 0.15s;
    }}
    .ann-feed-item:hover {{ background: rgba(255,255,255,0.03); }}
    .ann-feed-item:last-child {{ border-bottom: none; }}
    .ann-feed-cat {{
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.06em; color: #818cf8; margin-bottom: 3px;
    }}
    .ann-feed-title {{ font-size: 13px; font-weight: 600; color: #e0e0f0; line-height: 1.35; }}
    .ann-feed-time {{ font-size: 10px; color: #606078; margin-top: 3px; }}
    .ann-feed-footer {{
      text-align: center; padding: 8px; background: #0e0e1a;
      border-radius: 0 0 8px 8px; font-size: 10px; color: #606078;
    }}
    .ann-feed-footer a {{ color: #818cf8; text-decoration: none; }}
  `;

  function init() {{
    var el = document.getElementById('ann-feed');
    if (!el) return;

    var s = document.createElement('style');
    s.textContent = STYLE;
    document.head.appendChild(s);

    el.innerHTML = '<div class="ann-feed"><div class="ann-feed-header">📺 A.N.N. — AI News</div><div class="ann-feed-list" id="ann-feed-list">Loading...</div><div class="ann-feed-footer">Powered by <a href="' + ANN_API + '/news" target="_blank">A.N.N.</a></div></div>';

    fetch(ANN_API + '/api/v1/scripts?limit=8')
      .then(function(r) {{ return r.json(); }})
      .then(function(scripts) {{
        var list = document.getElementById('ann-feed-list');
        if (!scripts.length) {{
          list.innerHTML = '<div class="ann-feed-item"><div class="ann-feed-title">No news yet</div></div>';
          return;
        }}
        list.innerHTML = scripts.map(function(s) {{
          return '<div class="ann-feed-item" onclick="window.open(\\'' + ANN_API + '/news\\', \\'_blank\\')">' +
            '<div class="ann-feed-cat">' + esc(s.category) + '</div>' +
            '<div class="ann-feed-title">' + esc(s.headline) + '</div>' +
            '<div class="ann-feed-time">' + timeAgo(s.created_at) + '</div>' +
          '</div>';
        }}).join('');
      }})
      .catch(function() {{
        document.getElementById('ann-feed-list').innerHTML = '<div class="ann-feed-item"><div class="ann-feed-title">Feed unavailable</div></div>';
      }});
  }}

  function esc(t) {{
    var d = document.createElement('div');
    d.textContent = t || '';
    return d.innerHTML;
  }}

  function timeAgo(dt) {{
    if (!dt) return '';
    var diff = Math.floor((Date.now() - new Date(dt)) / 1000);
    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    return Math.floor(diff / 86400) + 'd ago';
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', init);
  }} else {{
    init();
  }}
}})();
"""
