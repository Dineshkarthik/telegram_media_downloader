"""Premium Design System CSS for the Telegram Media Downloader Web UI."""

PREMIUM_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
/* ── Design Tokens ───────────────────────────────────────────── */
:root {
    --surface:      #ffffff;
    --surface-dim:  #f8fafc;
    --surface-2:    #f1f5f9;
    --surface-3:    #e2e8f0;
    --border:       #e2e8f0;
    --border-light: #f1f5f9;
    --text-primary:   #0f172a;
    --text-secondary: #475569;
    --text-tertiary:  #94a3b8;
    --accent:       #6366f1;
    --accent-soft:  #eef2ff;
    --accent-hover: #4f46e5;
    --positive:     #10b981;
    --negative:     #ef4444;
    --warning:      #f59e0b;

    --q-primary:   #6366f1;
    --q-secondary: #64748b;
    --q-accent:    #8b5cf6;
    --q-positive:  #10b981;
    --q-negative:  #ef4444;
    --q-info:      #3b82f6;
    --q-warning:   #f59e0b;

    --radius-sm:  8px;
    --radius-md:  12px;
    --radius-lg:  16px;
    --radius-xl:  20px;
    --shadow-sm:  0 1px 2px rgba(0,0,0,0.04);
    --shadow-md:  0 2px 8px rgba(0,0,0,0.06), 0 0 1px rgba(0,0,0,0.04);
    --shadow-lg:  0 8px 24px rgba(0,0,0,0.08), 0 0 1px rgba(0,0,0,0.04);
    --transition: 150ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Dark Mode Tokens ────────────────────────────────────────── */
body.body--dark {
    --surface:      #0c111d;
    --surface-dim:  #111827;
    --surface-2:    #1e293b;
    --surface-3:    #334155;
    --border:       #1e293b;
    --border-light: #1e293b;
    --text-primary:   #f8fafc;
    --text-secondary: #94a3b8;
    --text-tertiary:  #64748b;
    --accent:       #818cf8;
    --accent-soft:  rgba(99,102,241,0.12);
    --accent-hover: #a5b4fc;
    --positive:     #34d399;
    --negative:     #f87171;
    --warning:      #fbbf24;
    --shadow-sm:  0 1px 2px rgba(0,0,0,0.2);
    --shadow-md:  0 2px 8px rgba(0,0,0,0.3), 0 0 1px rgba(0,0,0,0.1);
    --shadow-lg:  0 8px 24px rgba(0,0,0,0.4), 0 0 1px rgba(0,0,0,0.1);
}

/* ── Base Reset ──────────────────────────────────────────────── */
*:not(.q-icon):not(.material-icons):not(.notranslate) { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif !important; }
body { background: var(--surface-dim) !important; color: var(--text-primary) !important; transition: background var(--transition), color var(--transition); -webkit-font-smoothing: antialiased; }
.q-icon, .material-icons, .notranslate { font-family: 'Material Icons' !important; }

/* ── Sidebar ─────────────────────────────────────────────────── */
.sidebar {
    background: var(--surface) !important; border-right: 1px solid var(--border) !important;
    transition: background var(--transition), border-color var(--transition);
}
.nav-item {
    display: flex; align-items: center; gap: 10px; padding: 10px 16px;
    border-radius: var(--radius-md); color: var(--text-secondary); cursor: pointer;
    font-size: 14px; font-weight: 500; transition: all var(--transition);
    white-space: nowrap; user-select: none; text-decoration: none !important;
    margin: 2px 0;
}
.nav-item:hover { background: var(--surface-2); color: var(--text-primary); }
.nav-item.active { background: var(--accent-soft); color: var(--accent); font-weight: 600; }
.nav-item .q-icon { font-size: 20px; opacity: 0.7; }
.nav-item.active .q-icon { opacity: 1; }

/* ── Cards ───────────────────────────────────────────────────── */
.premium-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);
    transition: background var(--transition), border-color var(--transition), box-shadow var(--transition);
}
.premium-card:hover { box-shadow: var(--shadow-md); }

/* ── Section Header ──────────────────────────────────────────── */
.section-title { font-size: 20px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-primary); line-height: 1.3; }
.section-subtitle { font-size: 13px; font-weight: 400; color: var(--text-tertiary); line-height: 1.5; margin-top: 2px; }

/* ── Quasar Overrides ────────────────────────────────────────── */
.q-field--outlined .q-field__control { border-radius: var(--radius-md) !important; transition: border-color var(--transition) !important; }
.q-field--outlined .q-field__control:before { border-color: var(--border) !important; }
.q-field--outlined .q-field__control:hover:before { border-color: var(--text-tertiary) !important; }
.q-field--focused .q-field__control:after { border-color: var(--accent) !important; border-width: 2px !important; }
body.body--dark .q-field--outlined .q-field__control:before { border-color: var(--border) !important; }
.q-field__label { font-weight: 500 !important; font-size: 13px !important; }

.q-btn { border-radius: var(--radius-md) !important; font-weight: 600 !important; text-transform: none !important; letter-spacing: -0.01em !important; transition: all var(--transition) !important; }
.q-btn--unelevated { box-shadow: none !important; }

.q-checkbox__label { font-weight: 500 !important; }
.q-expansion-item__container { border-radius: var(--radius-md) !important; }

/* ── Tabs (Segmented Control) ────────────────────────────────── */
.q-tabs { background: transparent !important; }
.q-tab { border-radius: var(--radius-md) !important; min-height: 40px !important; font-weight: 500 !important; font-size: 13px !important; color: var(--text-tertiary) !important; letter-spacing: 0 !important; text-transform: none !important; padding: 0 20px !important; }
.q-tab--active { background: var(--accent-soft) !important; color: var(--accent) !important; font-weight: 600 !important; }
.q-tab__indicator { display: none !important; }

/* ── Table ────────────────────────────────────────────────────── */
.q-table__container { background: transparent !important; box-shadow: none !important; border-radius: var(--radius-md) !important; }
.q-table th { background: var(--surface-2) !important; color: var(--text-tertiary) !important; font-weight: 600 !important; font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; border-bottom: 1px solid var(--border) !important; padding: 10px 16px !important; }
.q-table td { color: var(--text-secondary) !important; font-size: 13px !important; border-bottom: 1px solid var(--border-light) !important; padding: 12px 16px !important; }
.q-table tbody tr:hover td { background: var(--surface-2) !important; }
.q-table__bottom { border-top: 1px solid var(--border-light) !important; }

/* ── Status Badges ───────────────────────────────────────────── */
.status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; letter-spacing: 0.02em; }
.status-idle { background: var(--surface-2); color: var(--text-tertiary); }
.status-running { background: rgba(59,130,246,0.1); color: #3b82f6; }
.status-success { background: rgba(16,185,129,0.1); color: var(--positive); }
.status-error { background: rgba(239,68,68,0.1); color: var(--negative); }
.status-warning { background: rgba(245,158,11,0.1); color: var(--warning); }

/* ── Progress Row ────────────────────────────────────────────── */
.dl-row { background: var(--surface); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 12px 16px; transition: all var(--transition); }
.dl-row:hover { border-color: var(--border); box-shadow: var(--shadow-sm); }

/* ── Terminal ────────────────────────────────────────────────── */
.terminal-log { background: #0f172a !important; color: #a3e635 !important; border-radius: var(--radius-md) !important; border: 1px solid #1e293b !important; font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', 'Cascadia Code', monospace !important; }
body.body--dark .terminal-log { background: #020617 !important; border-color: #1e293b !important; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

/* ── Chat Card ───────────────────────────────────────────────── */
.chat-card { background: var(--surface-dim); border: 1px solid var(--border); border-radius: var(--radius-md); padding: 16px; transition: all var(--transition); }
.chat-card:hover { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }

/* ── Misc ────────────────────────────────────────────────────── */
.label-sm { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.label-xs { font-size: 12px; font-weight: 500; color: var(--text-tertiary); }
.divider { height: 1px; background: var(--border); margin: 16px 0; border: none; }

/* Hide Quasar header since we use sidebar */
.q-header { display: none !important; }
.q-page-container { padding-top: 0 !important; }

/* Force tab panels to fill width */
.q-tab-panels, .q-tab-panel, .q-panel.scroll { width: 100% !important; }
.q-tab-panels .q-tab-panel > * { width: 100%; }
</style>
"""
