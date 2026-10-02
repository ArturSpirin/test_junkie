import math

from test_junkie.constants import TestCategory


_STATUS_COLORS = {
    TestCategory.SUCCESS: "#12d479",
    TestCategory.FAIL:    "#fcd75f",
    TestCategory.ERROR:   "#ff7651",
    TestCategory.SKIP:    "#34bff5",
    TestCategory.IGNORE:  "#cce4eb",
    TestCategory.CANCEL:  "#f19def",
}

_STATUS_LABELS = {
    TestCategory.SUCCESS: "Success",
    TestCategory.FAIL:    "Fail",
    TestCategory.ERROR:   "Error",
    TestCategory.SKIP:    "Skip",
    TestCategory.IGNORE:  "Ignore",
    TestCategory.CANCEL:  "Cancel",
}

_CSS = """\
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--brand:#f37814;--brand-strong:#e8660a;--canvas:#0d1117;--surface:#161b22;--surface-raised:#1c2129;--border:#2d333b;--border-strong:#444c56;--ink:#e6edf3;--ink-muted:#8b949e;--ink-faint:#6e7681;--s-success:#12d479;--s-fail:#fcd75f;--s-error:#ff7651;--s-ignore:#cce4eb;--s-skip:#34bff5;--s-cancel:#f19def}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{overflow-x:hidden}
body{background:var(--canvas);color:var(--ink);font-family:'IBM Plex Sans',-apple-system,BlinkMacSystemFont,sans-serif;font-size:14px;line-height:1.5;min-height:100vh}
a{color:var(--brand);text-decoration:none}
button{cursor:pointer;border:none;background:none;font-family:inherit}
.mono{font-family:'IBM Plex Mono','Courier New',monospace}
.container{max-width:1400px;margin:0 auto;padding:0 24px}
header{border-bottom:1px solid var(--border);background:var(--surface);position:sticky;top:0;z-index:100}
.header-inner{display:flex;align-items:center;justify-content:space-between;height:52px;gap:16px}
.brand{display:flex;align-items:center;gap:10px}
.brand-icon{width:28px;height:28px;flex:none}
.brand-name{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:var(--ink);letter-spacing:.04em}
.brand-name span{color:var(--brand)}
.header-meta{display:flex;align-items:center;gap:20px;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-faint);letter-spacing:.04em}
.run-status{display:flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}
.run-status-dot{width:6px;height:6px;border-radius:50%}
.stats-row{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;padding:20px 0 0}
@media(max-width:900px){.stats-row{grid-template-columns:repeat(3,1fr)}}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;position:relative;overflow:hidden}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--brand);opacity:0;transition:opacity .2s}
.stat-card:hover::before{opacity:1}
.stat-label{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace}
.stat-value{font-size:26px;font-weight:700;font-family:'IBM Plex Mono',monospace;color:var(--ink);line-height:1.2;margin-top:6px}
.stat-value.brand{color:var(--brand)}
.stat-sub{font-size:11px;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;margin-top:4px}
.charts-row{display:grid;grid-template-columns:1fr 340px;gap:12px;padding:12px 0 0}
@media(max-width:900px){.charts-row{grid-template-columns:1fr}}
.chart-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px}
.card-title{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;margin-bottom:12px}
.donut-wrap{display:flex;flex-direction:column;align-items:center;gap:16px}
.donut-svg{overflow:visible}
.donut-center-label{font-family:'IBM Plex Mono',monospace;text-anchor:middle;dominant-baseline:middle}
.resource-chart-wrap{width:100%}
.resource-chart-wrap svg{display:block;width:100%}
.resource-disabled{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-height:152px;text-align:center;border:1px dashed var(--border-strong);border-radius:8px;padding:24px}
.resource-disabled-icon{font-size:24px;opacity:.4}
.resource-disabled-msg{font-size:13px;color:var(--ink-muted);line-height:1.6}
.resource-disabled-msg code{font-family:'IBM Plex Mono',monospace;color:var(--brand);font-size:12px}
.resource-toggle-btn{font-size:10px;font-family:'IBM Plex Mono',monospace;font-weight:600;letter-spacing:.05em;padding:3px 9px;border-radius:5px;border:1px solid var(--border-strong);background:transparent;color:var(--ink-faint);cursor:pointer;transition:color .15s,border-color .15s}
.resource-toggle-btn:hover{color:var(--ink);border-color:var(--ink-muted)}
.bar-legend{display:flex;flex-wrap:wrap;gap:5px 14px;margin-bottom:18px}
.bar-legend-item{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--ink-muted);font-family:'IBM Plex Mono',monospace}
.bar-legend-swatch{width:10px;height:10px;border-radius:2px;flex:none}
.insights-list{display:flex;flex-direction:column;gap:10px}
.insight-item{display:flex;gap:10px;padding:10px 12px;background:var(--surface-raised);border-radius:6px;border-left:3px solid var(--border-strong);font-size:13px;color:var(--ink-muted);line-height:1.5}
.insight-item.warn{border-left-color:var(--s-fail)}
.insight-item.ok{border-left-color:var(--s-success)}
.insight-item.info{border-left-color:var(--brand)}
.insight-icon{flex:none;margin-top:1px}
.breakdown-section{padding:12px 0 0}
.breakdown-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.tab-bar{display:flex;border-bottom:1px solid var(--border);padding:0 20px;gap:4px}
.tab-btn{padding:12px 14px;font-size:12px;font-weight:600;letter-spacing:.04em;color:var(--ink-faint);border-bottom:2px solid transparent;margin-bottom:-1px;transition:color .15s,border-color .15s;font-family:'IBM Plex Mono',monospace}
.tab-btn:hover{color:var(--ink-muted)}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand)}
.tab-content{display:none;padding:24px 20px}
.tab-content.active{display:block}
.stacked-chart{display:flex;flex-direction:column;gap:14px}
.bar-row{display:flex;align-items:center;gap:14px}
.bar-label{width:150px;flex:none;font-size:12px;color:var(--ink-muted);font-family:'IBM Plex Mono',monospace;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{flex:1;height:22px;background:var(--surface-raised);border-radius:4px;overflow:hidden;display:flex}
.bar-segment{height:100%;transition:width .5s ease;position:relative}
.bar-segment:hover::after{content:attr(data-tip);position:absolute;bottom:28px;left:50%;transform:translateX(-50%);background:var(--surface-raised);border:1px solid var(--border);color:var(--ink);font-size:11px;padding:3px 8px;border-radius:4px;white-space:nowrap;pointer-events:none;z-index:10;font-family:'IBM Plex Mono',monospace}
.bar-meta{width:80px;flex:none;font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint)}
.results-section{padding:12px 0 24px}
.results-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.results-header{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid var(--border)}
.results-title{font-size:13px;font-weight:600;color:var(--ink);display:flex;align-items:center;gap:10px}
.results-count{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);background:var(--surface-raised);padding:2px 8px;border-radius:999px;border:1px solid var(--border)}
.search-global{display:flex;align-items:center;gap:8px;background:var(--surface-raised);border:1px solid var(--border);border-radius:6px;padding:6px 12px;font-size:12px;color:var(--ink-muted)}
.search-global input{background:none;border:none;outline:none;color:var(--ink);font-size:12px;font-family:'IBM Plex Mono',monospace;width:180px}
.search-global input::placeholder{color:var(--ink-faint)}
.filter-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 20px;border-bottom:1px solid var(--border);background:color-mix(in srgb,var(--surface-raised) 40%,var(--surface))}
.filter-label{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);flex:none;margin-right:4px}
.filter-dropdown{position:relative}
.filter-btn{display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:6px;background:var(--surface-raised);border:1px solid var(--border);color:var(--ink-muted);font-size:11px;font-family:'IBM Plex Mono',monospace;transition:border-color .12s,color .12s,background .12s;white-space:nowrap}
.filter-btn:hover{border-color:var(--border-strong);color:var(--ink)}
.filter-btn.has-value{border-color:var(--brand);background:color-mix(in srgb,var(--brand) 10%,var(--surface-raised));color:var(--brand)}
.filter-count{display:inline-flex;align-items:center;justify-content:center;min-width:16px;height:16px;padding:0 4px;background:var(--brand);color:#fff;border-radius:999px;font-size:9px;font-weight:700;font-family:'IBM Plex Mono',monospace}
.filter-chevron{transition:transform .15s;flex:none}
.filter-dropdown.open .filter-chevron{transform:rotate(180deg)}
.filter-menu{display:none;position:absolute;top:calc(100% + 6px);left:0;min-width:200px;background:var(--surface-raised);border:1px solid var(--border-strong);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.5);z-index:400;overflow:hidden}
.filter-dropdown.open .filter-menu{display:block}
.filter-menu-header{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--border);font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint)}
.filter-menu-clear{font-size:10px;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;text-transform:none;letter-spacing:0}
.filter-menu-clear:hover{color:var(--brand)}
.filter-menu-items{max-height:220px;overflow-y:auto;padding:4px 0}
.filter-menu-item{display:flex;align-items:center;gap:10px;padding:7px 12px;cursor:pointer;transition:background .1s}
.filter-menu-item:hover{background:color-mix(in srgb,var(--brand) 8%,var(--surface-raised))}
.filter-menu-item input[type=checkbox]{width:14px;height:14px;accent-color:var(--brand);cursor:pointer;flex:none}
.filter-menu-item label{font-size:12px;font-family:'IBM Plex Mono',monospace;color:var(--ink-muted);cursor:pointer;flex:1}
.filter-menu-item:hover label{color:var(--ink)}
.filter-menu-item .item-count{font-size:10px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint)}
.filter-clear-all{margin-left:auto;font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);padding:5px 8px;border-radius:6px;transition:color .12s,background .12s}
.filter-clear-all:hover{color:var(--brand);background:color-mix(in srgb,var(--brand) 8%,transparent)}
.filter-clear-all:not(.visible){visibility:hidden}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
thead th{padding:10px 14px;text-align:left;font-size:10px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);border-bottom:1px solid var(--border);white-space:nowrap;user-select:none;cursor:pointer;transition:color .12s}
thead th:hover{color:var(--ink-muted)}
thead th.sort-asc,thead th.sort-desc{color:var(--brand)}
thead th .sort-icon{display:inline-block;margin-left:4px;font-size:9px;opacity:.4}
thead th.sort-asc .sort-icon,thead th.sort-desc .sort-icon{opacity:1}
tbody tr{border-bottom:1px solid var(--border);cursor:pointer;transition:background .12s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:color-mix(in srgb,var(--brand) 5%,var(--surface))}
tbody tr.selected{background:color-mix(in srgb,var(--brand) 8%,var(--surface))}
tbody td{padding:9px 14px;color:var(--ink-muted);font-size:13px;white-space:nowrap}
tbody td.name-cell{color:var(--ink);font-family:'IBM Plex Mono',monospace;font-size:12px}
tbody td.suite-cell{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-faint)}
tbody td.mono-cell{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--ink-faint)}
.tag-chips{display:flex;flex-wrap:nowrap;gap:4px;align-items:center;overflow:hidden}
.tag-chip{display:inline-block;padding:1px 7px;border-radius:4px;flex:none;font-size:10px;font-weight:600;font-family:'IBM Plex Mono',monospace;background:color-mix(in srgb,var(--brand) 10%,var(--surface-raised));color:var(--ink-faint);border:1px solid color-mix(in srgb,var(--brand) 18%,var(--border));white-space:nowrap}
.variant-count-chip{display:inline-flex;align-items:center;gap:3px;flex:none;padding:1px 6px;border-radius:4px;margin-left:6px;font-size:10px;font-weight:600;font-family:'IBM Plex Mono',monospace;background:color-mix(in srgb,var(--brand) 12%,var(--surface-raised));color:var(--brand);border:1px solid color-mix(in srgb,var(--brand) 25%,var(--border));vertical-align:middle}
body.light .variant-count-chip{background:color-mix(in srgb,var(--brand) 10%,#fff);border-color:color-mix(in srgb,var(--brand) 30%,var(--border))}
.tag-overflow{display:inline-flex;align-items:center;justify-content:center;flex:none;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;font-family:'IBM Plex Mono',monospace;white-space:nowrap;background:var(--surface-raised);color:var(--ink-faint);border:1px solid var(--border)}
.panel-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.badge{display:inline-flex;align-items:center;gap:5px;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;font-family:'IBM Plex Mono',monospace;letter-spacing:.06em;text-transform:uppercase}
.badge-success{background:color-mix(in srgb,var(--s-success) 15%,transparent);color:var(--s-success)}
.badge-fail{background:color-mix(in srgb,var(--s-fail) 15%,transparent);color:var(--s-fail)}
.badge-error{background:color-mix(in srgb,var(--s-error) 15%,transparent);color:var(--s-error)}
.badge-skip{background:color-mix(in srgb,var(--s-skip) 15%,transparent);color:var(--s-skip)}
.badge-ignore{background:color-mix(in srgb,var(--s-ignore) 15%,transparent);color:var(--s-ignore)}
.badge-cancel{background:color-mix(in srgb,var(--s-cancel) 15%,transparent);color:var(--s-cancel)}
#detail-panel{position:fixed;top:52px;right:0;bottom:0;width:820px;background:var(--surface);border-left:1px solid var(--border);box-shadow:-8px 0 32px rgba(0,0,0,.5);z-index:200;display:flex;flex-direction:column;transform:translateX(100%);transition:transform .25s cubic-bezier(.4,0,.2,1);overflow:hidden}
#detail-panel.open{transform:translateX(0)}
.panel-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex:none}
.panel-test-name{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;color:var(--ink);word-break:break-all}
.panel-suite-path{font-size:11px;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;margin-top:3px}
.panel-close{flex:none;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:6px;color:var(--ink-muted);transition:background .12s,color .12s;font-size:18px;line-height:1}
.panel-close:hover{background:var(--surface-raised);color:var(--ink)}
.panel-body{flex:1;overflow-y:auto;padding:16px 20px}
.lifecycle-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:20px}
.lifecycle-card{background:var(--surface-raised);border:1px solid var(--border);border-radius:8px;padding:12px}
.lifecycle-card.has-failure{border-left:3px solid var(--s-error)}
.lifecycle-card-title{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;color:var(--brand);margin-bottom:10px}
.lifecycle-row{display:flex;justify-content:space-between;font-size:11px;padding:2px 0}
.lifecycle-key{color:var(--ink-faint)}
.lifecycle-val{font-family:'IBM Plex Mono',monospace;font-weight:600;color:var(--ink-muted)}
.variants-title{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;margin-bottom:10px}
.variant-item{border:1px solid var(--border);border-radius:8px;margin-bottom:8px;overflow:hidden}
.variant-header{display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--surface-raised);cursor:pointer;user-select:none;transition:background .12s}
.variant-header:hover{background:color-mix(in srgb,var(--brand) 6%,var(--surface-raised))}
.variant-param{flex:1;font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.variant-dur{font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint)}
.chevron{color:var(--ink-faint);transition:transform .2s;flex:none}
.variant-item.expanded .chevron{transform:rotate(90deg)}
.variant-body{display:none;padding:0 14px 14px}
.variant-item.expanded .variant-body{display:block}
.attempt{border:1px solid var(--border);border-radius:6px;margin-top:10px;overflow:hidden}
.attempt-header{display:flex;align-items:center;gap:10px;padding:8px 12px;background:color-mix(in srgb,var(--surface-raised) 60%,var(--surface));font-size:11px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);cursor:pointer;user-select:none}
.attempt-header span{color:var(--ink-muted)}
.attempt-body{display:none}
.attempt.expanded .attempt-body{display:block}
.trace-block{border-top:1px solid var(--border)}
.trace-label{padding:6px 12px;font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;border-bottom:1px solid var(--border)}
.trace-label.ok{color:var(--s-success);background:color-mix(in srgb,var(--s-success) 8%,transparent)}
.trace-label.bad{color:var(--s-error);background:color-mix(in srgb,var(--s-error) 8%,transparent)}
.trace-label.fail{color:var(--s-fail);background:color-mix(in srgb,var(--s-fail) 8%,transparent)}
.trace-label.na{color:var(--ink-faint);background:color-mix(in srgb,var(--ink-faint) 6%,transparent)}
.trace-body{padding:10px 12px;font-family:'IBM Plex Mono',monospace;font-size:11px;line-height:1.6;white-space:pre-wrap;word-break:break-all;background:#0a0e14}
.trace-body.ok{color:var(--s-success)}
.trace-body.bad{color:var(--s-error)}
.trace-body.fail{color:var(--s-fail)}
.trace-body.na{color:var(--ink-faint)}
.trace-runtime{text-align:right;padding:4px 12px;font-size:10px;font-family:'IBM Plex Mono',monospace;color:var(--ink-faint);background:color-mix(in srgb,var(--surface-raised) 40%,transparent)}
#overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:199}
#overlay.show{display:block}
#support-fab{position:fixed;bottom:28px;right:28px;z-index:150;width:52px;height:52px;border-radius:50%;background:var(--brand);color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 20px rgba(243,120,20,.45);transition:transform .15s,box-shadow .15s;border:none;cursor:pointer}
#support-fab:hover{transform:scale(1.08);box-shadow:0 6px 28px rgba(243,120,20,.6)}
#support-fab::after{content:'';position:absolute;inset:-4px;border-radius:50%;border:2px solid var(--brand);opacity:.3;animation:fab-pulse 2.4s ease-out infinite}
@keyframes fab-pulse{0%{transform:scale(1);opacity:.3}70%{transform:scale(1.35);opacity:0}100%{transform:scale(1.35);opacity:0}}
#support-backdrop{display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:500;backdrop-filter:blur(2px)}
#support-backdrop.show{display:block}
#support-modal{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-48%) scale(.97);z-index:501;width:min(440px,calc(100vw - 32px));background:var(--surface);border:1px solid var(--border-strong);border-radius:14px;padding:28px 24px 24px;box-shadow:0 24px 64px rgba(0,0,0,.6);opacity:0;transition:opacity .2s,transform .2s}
#support-modal.show{display:block;opacity:1;transform:translate(-50%,-50%) scale(1)}
.support-close{position:absolute;top:14px;right:14px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:6px;font-size:16px;color:var(--ink-faint);transition:background .12s,color .12s}
.support-close:hover{background:var(--surface-raised);color:var(--ink)}
.support-logo{display:flex;justify-content:center;margin-bottom:12px}
.support-title{text-align:center;font-size:16px;font-weight:700;color:var(--ink);margin-bottom:10px;font-family:'IBM Plex Mono',monospace}
.support-message{text-align:center;font-size:13px;color:var(--ink-muted);line-height:1.6;margin-bottom:20px}
.support-options{display:flex;flex-direction:column;gap:8px}
.support-option{display:flex;align-items:center;gap:14px;padding:12px 14px;background:var(--surface-raised);border:1px solid var(--border);border-radius:8px;text-decoration:none;transition:border-color .12s,background .12s,transform .1s}
.support-option:hover{border-color:var(--brand);background:color-mix(in srgb,var(--brand) 5%,var(--surface-raised));transform:translateX(2px)}
.support-option-icon{width:36px;height:36px;border-radius:8px;background:var(--surface);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;color:var(--ink-muted);flex:none}
.support-option-text{flex:1}
.support-option-label{font-size:13px;font-weight:600;color:var(--ink)}
.support-option-sub{font-size:11px;color:var(--ink-faint);margin-top:2px}
.support-option-arrow{color:var(--ink-faint);flex:none}
body.light{--canvas:#f6f8fa;--surface:#ffffff;--surface-raised:#f0f2f5;--border:#d0d7de;--border-strong:#adb5bd;--ink:#1a1f2e;--ink-muted:#444c56;--ink-faint:#6e7681}
body.light .trace-body{background:#f6f8fa}
body.light .run-status{background:color-mix(in srgb,var(--s-fail) 8%,var(--surface-raised))}
body.light .badge-success{background:#d4f7e7;color:#0a6b3b}
body.light .badge-fail{background:#fff0c4;color:#7a5200}
body.light .badge-error{background:#fde5dc;color:#b83000}
body.light .badge-skip{background:#d9f3ff;color:#005f96}
body.light .badge-ignore{background:#dde8ec;color:#3a5f6e}
body.light .badge-cancel{background:#fce5f8;color:#800070}
body.light .tag-chip{background:color-mix(in srgb,var(--brand) 12%,#fff);color:var(--brand-strong);border-color:color-mix(in srgb,var(--brand) 30%,var(--border))}
.theme-toggle{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:6px;color:var(--ink-faint);transition:background .12s,color .12s;border:1px solid var(--border)}
.theme-toggle:hover{background:var(--surface-raised);color:var(--ink)}
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-strong);border-radius:3px}
</style>"""

_BRAND_SVG = """\
<svg class="brand-icon" viewBox="0 0 28 28" fill="none">
  <circle cx="14" cy="14" r="11" stroke="#f37814" stroke-width="1.4" stroke-dasharray="5 3" opacity=".6"/>
  <path d="M 25,14 A 11,11 0 0,0 14,3" stroke="#f37814" stroke-width="3" stroke-linecap="round"/>
  <circle cx="14" cy="14" r="6" stroke="#f37814" stroke-width="2"/>
  <line x1="3" y1="14" x2="8" y2="14" stroke="#f37814" stroke-width="1.6"/>
  <line x1="20" y1="14" x2="25" y2="14" stroke="#f37814" stroke-width="1.6"/>
  <line x1="14" y1="3" x2="14" y2="8" stroke="#f37814" stroke-width="1.6"/>
  <line x1="14" y1="20" x2="14" y2="25" stroke="#f37814" stroke-width="1.6"/>
  <polygon points="14,10 17,14 14,18 11,14" fill="#f37814"/>
  <circle cx="14" cy="14" r="1.5" fill="white" opacity=".9"/>
</svg>"""


class ReportTemplate:

    @staticmethod
    def render(data):
        ctx = ReportTemplate._build_context(data)
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>Test Junkie — Run Report</title>\n'
            + _CSS + '\n</head>\n<body>\n'
            + ReportTemplate._header(ctx)
            + '<div class="container">\n'
            + ReportTemplate._stats(ctx)
            + ReportTemplate._charts_row(ctx)
            + ReportTemplate._breakdown(ctx)
            + ReportTemplate._results_section()
            + '</div>\n'
            + ReportTemplate._detail_panel()
            + ReportTemplate._support_fab()
            + ReportTemplate._support_modal()
            + ReportTemplate._scripts(ctx)
            + '</body>\n</html>\n'
        )

    # ── Context builder ───────────────────────────────────────────────────────

    @staticmethod
    def _build_context(data):
        totals = data["totals"]
        issues = data["issues"]

        if issues > 0:
            issue_badge = (
                f'<div class="run-status" style="background:color-mix(in srgb,var(--s-fail) 12%,'
                f'var(--surface-raised));border:1px solid color-mix(in srgb,var(--s-fail) 30%,'
                f'var(--border));color:var(--s-fail)">'
                f'<div class="run-status-dot" style="background:var(--s-fail)"></div>'
                f'{issues} issue{"s" if issues != 1 else ""}</div>'
            )
        else:
            issue_badge = (
                '<div class="run-status" style="background:color-mix(in srgb,var(--s-success) 12%,'
                'var(--surface-raised));border:1px solid color-mix(in srgb,var(--s-success) 30%,'
                'var(--border));color:var(--s-success)">'
                '<div class="run-status-dot" style="background:var(--s-success)"></div>stable</div>'
            )

        n_success = totals.get(TestCategory.SUCCESS, 0)
        n_total = totals.get("total", 0)
        suite_count = data.get("suite_count", 0)

        cpu_avg = data.get("cpu_avg", "—")
        cpu_peak = data.get("cpu_peak", "—")
        mem_avg = data.get("mem_avg", "—")
        mem_peak = data.get("mem_peak", "—")
        resources_enabled = data.get("resources_enabled", False)

        cpu_sub = f"peak {cpu_peak}" if cpu_peak != "—" else "not tracked"
        mem_sub = f"peak {mem_peak}" if mem_peak != "—" else "not tracked"

        runtime_str = data.get("runtime", "—")
        if resources_enabled:
            res_legend_style = ""
            res_enabled_style = ""
            res_disabled_style = "display:none"
            res_toggle_text = "Disable"
        else:
            res_legend_style = "display:none"
            res_enabled_style = "display:none"
            res_disabled_style = ""
            res_toggle_text = "Enable"

        return {
            "run_date": data.get("run_date", ""),
            "run_time": data.get("run_time", ""),
            "runtime": runtime_str,
            "issue_badge": issue_badge,
            "stat_total": str(n_total),
            "stat_suite_count": f"across {suite_count} suite{'s' if suite_count != 1 else ''}",
            "stat_passing_rate": totals.get("passing_rate", "0.0%"),
            "stat_passing_sub": f"{n_success} of {n_total} passed",
            "stat_runtime": runtime_str,
            "stat_avg_runtime": data.get("avg_runtime", "—"),
            "stat_cpu_avg": cpu_avg,
            "stat_cpu_sub": cpu_sub,
            "stat_mem_avg": mem_avg,
            "stat_mem_sub": mem_sub,
            "res_legend_style": res_legend_style,
            "res_enabled_style": res_enabled_style,
            "res_disabled_style": res_disabled_style,
            "res_toggle_text": res_toggle_text,
            "resource_svg": data.get("resource_svg", ""),
            "insights_html": ReportTemplate._build_insights(data.get("insights", [])),
            "donut_html": ReportTemplate._build_donut(totals),
            "totals": totals,
            "tests_json": data.get("tests_json", "[]"),
            "details_json": data.get("details_json", "{}"),
            "bar_data_json": data.get("bar_data_json", "{}"),
        }

    # ── Donut SVG ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_donut(totals):
        circ = 2 * math.pi * 72
        status_order = [
            (TestCategory.SUCCESS, "#12d479", "Success"),
            (TestCategory.FAIL,    "#fcd75f", "Fail"),
            (TestCategory.ERROR,   "#ff7651", "Error"),
            (TestCategory.SKIP,    "#34bff5", "Skip"),
            (TestCategory.IGNORE,  "#cce4eb", "Ignore"),
            (TestCategory.CANCEL,  "#f19def", "Cancel"),
        ]
        total = totals.get("total", 0)
        avg_dur = totals.get("avg_dur", {})

        if total == 0:
            return '<div style="padding:20px;text-align:center;color:var(--ink-faint)">No test data.</div>'

        circles = ['<circle cx="90" cy="90" r="72" fill="none" stroke="#1c2129" stroke-width="22"/>']
        table_rows = []
        offset = 0.0

        col_header = (
            '<div style="display:grid;grid-template-columns:1fr 60px 60px 80px;gap:0;'
            'border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:6px;">'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace">Status</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">Count</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">%</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">Avg dur</span>'
            '</div>'
        )

        active_statuses = [(s, c, l) for s, c, l in status_order if totals.get(s, 0) > 0]
        last_idx = len(active_statuses) - 1

        for i, (status, color, label) in enumerate(active_statuses):
            count = totals.get(status, 0)
            arc = count / total * circ
            circles.append(
                f'<circle cx="90" cy="90" r="72" fill="none" stroke="{color}" stroke-width="22" '
                f'stroke-dasharray="{arc:.1f} {circ:.1f}" stroke-dashoffset="-{offset:.1f}" '
                f'transform="rotate(-90 90 90)" stroke-linecap="butt"/>'
            )
            pct = count / total * 100
            dur = avg_dur.get(status, "—")
            border = "" if i == last_idx else "border-bottom:1px solid var(--border);"
            table_rows.append(
                f'<div style="display:grid;grid-template-columns:1fr 60px 60px 80px;gap:0;'
                f'align-items:center;padding:5px 0;{border}">'
                f'<span style="display:flex;align-items:center;gap:7px;font-size:12px;color:var(--ink-muted)">'
                f'<span style="width:8px;height:8px;border-radius:2px;background:{color};'
                f'display:inline-block;flex:none"></span>{label}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;font-weight:600;'
                f'color:var(--ink);text-align:right">{count}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;'
                f'color:var(--ink-muted);text-align:right">{pct:.1f}%</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;'
                f'color:var(--ink-muted);text-align:right">{dur}</span>'
                f'</div>'
            )
            offset += arc

        circles_svg = "\n".join(circles)
        table_html = "\n".join(table_rows)
        return (
            '<div style="display:flex;align-items:center;gap:48px;justify-content:center;padding:8px 0;">'
            '<div style="flex:none">'
            f'<svg class="donut-svg" width="160" height="160" viewBox="0 0 180 180">'
            f'{circles_svg}'
            f'<text x="90" y="84" class="donut-center-label" fill="#e6edf3" font-size="26" font-weight="700" '
            f'font-family="\'IBM Plex Mono\',monospace">{total}</text>'
            f'<text x="90" y="102" class="donut-center-label" fill="#6e7681" font-size="11" '
            f'font-family="\'IBM Plex Mono\',monospace">tests</text>'
            f'</svg></div>'
            '<div style="display:flex;flex-direction:column;gap:0;min-width:260px;">'
            + col_header + table_html +
            '</div></div>'
        )

    # ── Insights ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_insights(insights):
        if not insights:
            return (
                '<div class="insight-item ok">'
                '<div class="insight-icon">✓</div>'
                '<div>All tests completed. No significant issues detected.</div>'
                '</div>'
            )
        parts = []
        for text in insights:
            tl = text.lower()
            if "stable" in tl or "no time" in tl:
                cls, icon = "ok", "✓"
            elif "retr" in tl or "traceback" in tl or "unique" in tl:
                cls, icon = "warn", "⚠"
            else:
                cls, icon = "info", "▸"
            import html as _html
            safe = _html.escape(text)
            parts.append(
                f'<div class="insight-item {cls}">'
                f'<div class="insight-icon">{icon}</div>'
                f'<div>{safe}</div></div>'
            )
        return "\n".join(parts)

    # ── Header ────────────────────────────────────────────────────────────────

    @staticmethod
    def _header(ctx):
        return (
            '<header>\n<div class="container header-inner">\n'
            f'<a class="brand" href="https://www.test-junkie.com" target="_blank" rel="noopener" style="text-decoration:none">'
            f'{_BRAND_SVG}'
            f'<span class="brand-name">TEST<span>JUNKIE</span></span>'
            f'</a>\n'
            f'<div class="header-meta">'
            f'<span>{ctx["run_date"]} &middot; {ctx["run_time"]}</span>'
            f'<span>{ctx["runtime"]} total</span>'
            f'{ctx["issue_badge"]}'
            f'<button class="theme-toggle" id="theme-toggle" title="Toggle light / dark mode">'
            f'<svg id="theme-icon-dark" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            f'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/>'
            f'<line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
            f'<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
            f'<line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>'
            f'<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>'
            f'<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
            f'<svg id="theme-icon-light" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none">'
            f'<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
            f'</button>'
            f'</div>\n'
            f'</div>\n</header>\n'
        )

    # ── Stat cards ────────────────────────────────────────────────────────────

    @staticmethod
    def _stats(ctx):
        def card(label, value, sub, brand=False):
            cls = 'stat-value brand' if brand else 'stat-value'
            return (
                f'<div class="stat-card">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="{cls}">{value}</div>'
                f'<div class="stat-sub">{sub}</div>'
                f'</div>'
            )
        return (
            '<div class="stats-row">\n'
            + card("Tests Executed", ctx["stat_total"], ctx["stat_suite_count"])
            + card("Passing Rate", ctx["stat_passing_rate"], ctx["stat_passing_sub"], brand=True)
            + card("Total Runtime", ctx["stat_runtime"], "wall-clock time")
            + card("Avg Test Runtime", ctx["stat_avg_runtime"], "@test only")
            + card("Avg CPU", ctx["stat_cpu_avg"], ctx["stat_cpu_sub"])
            + card("Avg Memory", ctx["stat_mem_avg"], ctx["stat_mem_sub"])
            + '\n</div>\n'
        )

    # ── Charts row ────────────────────────────────────────────────────────────

    @staticmethod
    def _charts_row(ctx):
        resource_body = (
            f'<div id="res-enabled" class="resource-chart-wrap" style="{ctx["res_enabled_style"]}">'
            + ctx["resource_svg"]
            + '</div>\n'
            '<div id="res-disabled" class="resource-disabled"'
            f' style="{ctx["res_disabled_style"]}">'
            '<div class="resource-disabled-icon">&#x1F4CA;</div>'
            '<div class="resource-disabled-msg">'
            'Resource monitoring was not enabled for this run.<br>'
            'To track CPU and memory usage, pass<br>'
            '<code>monitor_resources=True</code> to your runner.'
            '</div></div>\n'
        )
        return (
            '<div class="charts-row">\n'
            '<div class="chart-card" style="display:flex;flex-direction:column;">\n'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
            '<div class="card-title" style="margin-bottom:0">Resource Monitoring</div>'
            '<div style="display:flex;align-items:center;gap:14px;">'
            f'<div id="res-legend" style="display:flex;align-items:center;gap:14px;{ctx["res_legend_style"]}">'
            '<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:\'IBM Plex Mono\',monospace;color:var(--ink-muted)">'
            '<span style="display:inline-block;width:18px;height:2px;background:var(--brand);border-radius:1px;vertical-align:middle"></span>CPU</span>'
            '<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:\'IBM Plex Mono\',monospace;color:var(--ink-muted)">'
            '<span style="display:inline-block;width:18px;height:2px;background:#34bff5;border-radius:1px;vertical-align:middle"></span>Memory</span>'
            '</div>'
            f'<button class="resource-toggle-btn" id="res-toggle-btn" onclick="toggleResources()">{ctx["res_toggle_text"]}</button>'
            '</div></div>\n'
            + resource_body
            + '</div>\n'
            '<div class="chart-card">\n'
            '<div class="card-title">Insights</div>'
            '<div class="insights-list">'
            + ctx["insights_html"]
            + '</div></div>\n'
            '</div>\n'
        )

    # ── Breakdown tabs ────────────────────────────────────────────────────────

    @staticmethod
    def _breakdown(ctx):
        return (
            '<div class="breakdown-section">\n'
            '<div class="breakdown-card">\n'
            '<div class="tab-bar">'
            '<button class="tab-btn" data-tab="results">Results</button>'
            '<button class="tab-btn active" data-tab="features">Features</button>'
            '<button class="tab-btn" data-tab="components">Components</button>'
            '<button class="tab-btn" data-tab="owners">Owners</button>'
            '<button class="tab-btn" data-tab="suites">Suites</button>'
            '<button class="tab-btn" data-tab="tags">Tags</button>'
            '</div>\n'
            f'<div class="tab-content" id="tab-results">{ctx["donut_html"]}</div>\n'
            '<div class="tab-content active" id="tab-features"><div id="chart-features"></div></div>\n'
            '<div class="tab-content" id="tab-components"><div id="chart-components"></div></div>\n'
            '<div class="tab-content" id="tab-owners"><div id="chart-owners"></div></div>\n'
            '<div class="tab-content" id="tab-suites"><div id="chart-suites"></div></div>\n'
            '<div class="tab-content" id="tab-tags"><div id="chart-tags"></div></div>\n'
            '</div>\n</div>\n'
        )

    # ── Results table section ─────────────────────────────────────────────────

    @staticmethod
    def _results_section():
        return (
            '<div class="results-section">\n'
            '<div class="results-card">\n'
            '<div class="results-header">'
            '<div class="results-title">Test Results'
            '<span class="results-count" id="visible-count">— tests</span>'
            '</div>'
            '<div class="search-global">'
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'
            '<input type="text" id="global-search" placeholder="Search all columns…">'
            '</div></div>\n'
            '<div class="filter-bar" id="filter-bar">'
            '<span class="filter-label">Filters</span>'
            '<button class="filter-clear-all" id="clear-all-btn">Clear all \xd7</button>'
            '</div>\n'
            '<div class="table-wrap">'
            '<table id="results-table">'
            '<thead><tr id="table-head"></tr></thead>'
            '<tbody id="table-body"></tbody>'
            '</table></div>\n'
            '</div>\n</div>\n'
        )

    # ── Detail panel ──────────────────────────────────────────────────────────

    @staticmethod
    def _detail_panel():
        return (
            '<div id="overlay"></div>\n'
            '<div id="detail-panel">\n'
            '<div class="panel-header">'
            '<div style="flex:1;min-width:0">'
            '<div class="panel-test-name" id="panel-test-name">—</div>'
            '<div class="panel-suite-path" id="panel-suite-path">—</div>'
            '<div class="panel-tags" id="panel-tags"></div>'
            '</div>'
            '<button class="panel-close" id="panel-close">✕</button>'
            '</div>\n'
            '<div class="panel-body" id="panel-body"></div>\n'
            '</div>\n'
        )

    # ── Support FAB ───────────────────────────────────────────────────────────

    @staticmethod
    def _support_fab():
        return (
            '<button id="support-fab" title="Support this project" aria-label="Support this project">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 '
            '7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
            '</svg></button>\n'
        )

    # ── Support modal ─────────────────────────────────────────────────────────

    @staticmethod
    def _support_modal():
        logo = _BRAND_SVG.replace('class="brand-icon"', 'width="32" height="32"')
        return (
            '<div id="support-backdrop"></div>\n'
            '<div id="support-modal" role="dialog" aria-modal="true" aria-labelledby="support-title">\n'
            '<button class="support-close" id="support-close" aria-label="Close">✕</button>\n'
            f'<div class="support-logo">{logo}</div>\n'
            '<h2 class="support-title" id="support-title">Support Test Junkie</h2>\n'
            '<p class="support-message">Test Junkie is a solo open-source project. If it has saved you '
            'time writing runners, fighting flaky tests, or debugging parallel execution — '
            'a star or a coffee goes a long way and helps keep it maintained.</p>\n'
            '<div class="support-options">\n'
            '<a class="support-option" href="https://github.com/ArturSpirin/test_junkie" target="_blank" rel="noopener">'
            '<div class="support-option-icon">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 '
            '0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 '
            '1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 '
            '0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 '
            '1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 '
            '1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 '
            '0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Star on GitHub</div>'
            '<div class="support-option-sub">Show you use it \xb7 costs nothing</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '<a class="support-option" href="https://www.patreon.com/join/arturspirin" target="_blank" rel="noopener">'
            '<div class="support-option-icon" style="color:#ff424d">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M22.957 7.21c-.004-3.064-2.391-5.576-5.191-6.482-3.478-1.125-8.064-.962-11.384.604C2.357 3.231 '
            '1.093 7.391 1.046 11.54c-.039 3.411.302 12.396 5.369 12.46 3.765.047 4.326-4.804 6.068-7.141 '
            '1.24-1.662 2.836-2.132 4.801-2.618 3.376-.836 5.678-3.501 5.673-7.031Z"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Support on Patreon</div>'
            '<div class="support-option-sub">Monthly support \xb7 keeps the lights on</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '<a class="support-option" href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&amp;business=FJPYWX5B776YS&amp;currency_code=USD&amp;source=url" target="_blank" rel="noopener">'
            '<div class="support-option-icon" style="color:#009cde">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M7.016 19.198h-4.2a.562.562 0 0 1-.555-.65L5.093.584A.692.692 0 0 1 5.776 0h7.222c3.417 '
            '0 5.904 2.488 5.846 5.5-.006.25-.027.5-.066.747A6.794 6.794 0 0 1 12.071 12H8.743a.69.69 0 0 '
            '0-.682.583l-.325 2.056-.013.083-.692 4.39-.015.087zM19.79 6.142c-.01.087-.01.175-.023.261a7.76 '
            '7.76 0 0 1-7.695 6.598H9.007l-.283 1.795-.013.083-.692 4.39-.134.843-.014.088H6.86l-.497 3.15a.562.562 '
            '0 0 0 .555.65h3.612c.34 0 .63-.249.683-.585l.952-6.031a.692.692 0 0 1 .683-.584h2.126a6.793 6.793 '
            '0 0 0 6.707-5.752c.306-1.95-.466-3.744-1.89-4.906z"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Donate via PayPal</div>'
            '<div class="support-option-sub">One-time \xb7 any amount appreciated</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '</div>\n</div>\n'
        )

    # ── Scripts ───────────────────────────────────────────────────────────────

    @staticmethod
    def _scripts(ctx):
        tests_json = ctx["tests_json"].replace("</", "<\\/")
        details_json = ctx["details_json"].replace("</", "<\\/")
        bar_data_json = ctx["bar_data_json"].replace("</", "<\\/")

        return """<script>
const TESTS = """ + tests_json + """;
const DETAILS = """ + details_json + """;
const BAR_DATA = """ + bar_data_json + """;

/* ══ Column definitions ═══════════════════════════════════ */
const COLUMNS = [
  { key:'suite',     label:'Suite',     cls:'suite-cell', accessor: t => t.suite     },
  { key:'test',      label:'Test',      cls:'name-cell',  accessor: t => t.test      },
  { key:'feature',   label:'Feature',   cls:'',           accessor: t => t.feature   },
  { key:'component', label:'Component', cls:'',           accessor: t => t.component },
  { key:'owner',     label:'Owner',     cls:'',           accessor: t => t.owner     },
  { key:'tags',      label:'Tags',      cls:'',           accessor: t => t.tags, sortAccessor: t => (t.tags||[]).join(',') },
  { key:'started',   label:'Started',   cls:'mono-cell',  accessor: t => t.started   },
  { key:'ended',     label:'Ended',     cls:'mono-cell',  accessor: t => t.ended     },
  { key:'duration',  label:'Duration',  cls:'mono-cell',  accessor: t => t.duration, sortAccessor: t => t.durationSec },
  { key:'retries',   label:'Retries',   cls:'mono-cell',  accessor: t => t.retries,  sortAccessor: t => t.retries     },
  { key:'status',    label:'Status',    cls:'',           accessor: t => t.status    },
];

let sortKey = 'started';
let sortDir = 'asc';

const FILTER_FIELDS = ['suite','feature','component','owner','tags','status'];
const activeFilters = {};
FILTER_FIELDS.forEach(f => activeFilters[f] = new Set());

function getDistinct(field) {
  if (field === 'tags') return [...new Set(TESTS.flatMap(t => t.tags||[]))].sort();
  return [...new Set(TESTS.map(t => t[field]))].sort();
}
function countForValue(field, val) {
  if (field === 'tags') return TESTS.filter(t => (t.tags||[]).includes(val)).length;
  return TESTS.filter(t => t[field] === val).length;
}

function buildFilterBar() {
  const bar = document.getElementById('filter-bar');
  const clearBtn = document.getElementById('clear-all-btn');
  FILTER_FIELDS.forEach(field => {
    const values = getDistinct(field);
    const wrap = document.createElement('div');
    wrap.className = 'filter-dropdown';
    wrap.id = 'fd-' + field;
    const label = field.charAt(0).toUpperCase() + field.slice(1);
    wrap.innerHTML = `
      <button class="filter-btn" id="fb-${field}">
        ${label}
        <span class="filter-count" id="fc-${field}" style="display:none"></span>
        <svg class="filter-chevron" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>
      <div class="filter-menu" id="fm-${field}">
        <div class="filter-menu-header">
          ${label}
          <button class="filter-menu-clear" data-field="${field}">Clear</button>
        </div>
        <div class="filter-menu-items" id="fmi-${field}">
          ${values.map(v => `
            <div class="filter-menu-item">
              <input type="checkbox" id="chk-${field}-${v}" value="${v}" data-field="${field}">
              <label for="chk-${field}-${v}">${v}</label>
              <span class="item-count">${countForValue(field, v)}</span>
            </div>`).join('')}
        </div>
      </div>`;
    bar.insertBefore(wrap, clearBtn);
    wrap.querySelector('.filter-btn').addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = wrap.classList.contains('open');
      document.querySelectorAll('.filter-dropdown.open').forEach(d => d.classList.remove('open'));
      if (!isOpen) wrap.classList.add('open');
    });
    wrap.querySelectorAll('input[type=checkbox]').forEach(chk => {
      chk.addEventListener('change', () => {
        const f = chk.dataset.field;
        if (chk.checked) activeFilters[f].add(chk.value);
        else             activeFilters[f].delete(chk.value);
        updateFilterBtnState(f);
        applyAndRender();
      });
    });
    wrap.querySelector('.filter-menu-clear').addEventListener('click', e => {
      e.stopPropagation();
      clearField(field);
    });
  });
  document.addEventListener('click', () => {
    document.querySelectorAll('.filter-dropdown.open').forEach(d => d.classList.remove('open'));
  });
  document.querySelectorAll('.filter-menu').forEach(m => {
    m.addEventListener('click', e => e.stopPropagation());
  });
}

function updateFilterBtnState(field) {
  const btn = document.getElementById('fb-' + field);
  const countEl = document.getElementById('fc-' + field);
  const n = activeFilters[field].size;
  if (n > 0) {
    btn.classList.add('has-value');
    countEl.textContent = n;
    countEl.style.display = '';
  } else {
    btn.classList.remove('has-value');
    countEl.style.display = 'none';
  }
  updateClearAllVisibility();
}
function updateClearAllVisibility() {
  const anyActive = FILTER_FIELDS.some(f => activeFilters[f].size > 0);
  document.getElementById('clear-all-btn').classList.toggle('visible', anyActive);
}
function clearField(field) {
  activeFilters[field].clear();
  document.querySelectorAll(`input[data-field="${field}"]`).forEach(c => c.checked = false);
  updateFilterBtnState(field);
  applyAndRender();
}
document.getElementById('clear-all-btn').addEventListener('click', () => {
  FILTER_FIELDS.forEach(f => clearField(f));
});

function buildTableHead() {
  const tr = document.getElementById('table-head');
  tr.innerHTML = COLUMNS.map(col => {
    const isSorted = col.key === sortKey;
    const icon = isSorted ? (sortDir === 'asc' ? '▲' : '▼') : '⇅';
    const cls = isSorted ? (sortDir === 'asc' ? 'sort-asc' : 'sort-desc') : '';
    return `<th data-sort="${col.key}" class="${cls}">${col.label} <span class="sort-icon">${icon}</span></th>`;
  }).join('');
  tr.querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      if (sortKey === key) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      else { sortKey = key; sortDir = 'asc'; }
      buildTableHead();
      applyAndRender();
    });
  });
}

function applyAndRender() {
  const global = (document.getElementById('global-search').value || '').toLowerCase();
  let rows = TESTS.filter(t => {
    for (const field of FILTER_FIELDS) {
      if (activeFilters[field].size === 0) continue;
      if (field === 'tags') {
        if (!(t.tags||[]).some(tag => activeFilters[field].has(tag))) return false;
      } else {
        if (!activeFilters[field].has(t[field])) return false;
      }
    }
    if (global) {
      const haystack = COLUMNS.map(c => {
        const v = c.accessor(t);
        return Array.isArray(v) ? v.join(' ') : String(v);
      }).join(' ').toLowerCase();
      if (!haystack.includes(global)) return false;
    }
    return true;
  });
  const col = COLUMNS.find(c => c.key === sortKey);
  if (col) {
    const acc = col.sortAccessor || col.accessor;
    rows = [...rows].sort((a, b) => {
      const va = acc(a), vb = acc(b);
      if (va < vb) return sortDir === 'asc' ? -1 : 1;
      if (va > vb) return sortDir === 'asc' ?  1 : -1;
      return 0;
    });
  }
  renderTable(rows);
}

function badgeHtml(status) {
  return `<span class="badge badge-${status}">${status}</span>`;
}

function renderTable(rows) {
  const tbody = document.getElementById('table-body');
  tbody.innerHTML = rows.map(t => {
    const cells = COLUMNS.map(col => {
      let val = col.accessor(t);
      if (col.key === 'test' && t.variantCount > 1) {
        val = `${val}<span class="variant-count-chip">⊞ ×${t.variantCount}</span>`;
      } else if (col.key === 'tags') {
        const MAX = 1;
        const visible = (t.tags||[]).slice(0, MAX);
        const extra = (t.tags||[]).length - MAX;
        const chips = visible.map(tag => `<span class="tag-chip">${tag}</span>`).join('');
        const overflow = extra > 0 ? `<span class="tag-overflow">+${extra}</span>` : '';
        val = `<div class="tag-chips">${chips}${overflow}</div>`;
      } else if (col.key === 'status') {
        val = badgeHtml(t.status);
      } else if (col.key === 'retries') {
        val = t.retries > 0
          ? `<span style="color:var(--s-error);font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600">${t.retries}</span>`
          : `<span style="color:var(--ink-faint);font-family:'IBM Plex Mono',monospace;font-size:12px">0</span>`;
      }
      return `<td class="${col.cls}">${val}</td>`;
    }).join('');
    return `<tr data-id="${t.id}">${cells}</tr>`;
  }).join('');
  document.getElementById('visible-count').textContent = rows.length + ' test' + (rows.length !== 1 ? 's' : '');
  tbody.querySelectorAll('tr').forEach(tr => {
    tr.addEventListener('click', () => openPanel(parseInt(tr.dataset.id)));
  });
}

function renderBars(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container || !data || !data.length) return;
  const statuses = ['success','fail','error','skip','ignore','cancel'];
  const colors   = { success:'#12d479', fail:'#fcd75f', error:'#ff7651', skip:'#34bff5', ignore:'#cce4eb', cancel:'#f19def' };
  const labels   = { success:'Success', fail:'Fail', error:'Error', skip:'Skip', ignore:'Ignore', cancel:'Cancel' };
  const usedStatuses = statuses.filter(s => data.some(d => d[s] > 0));
  const legend = `<div class="bar-legend">${usedStatuses.map(s =>
    `<span class="bar-legend-item"><span class="bar-legend-swatch" style="background:${colors[s]}"></span>${labels[s]}</span>`
  ).join('')}</div>`;
  const rows = data.map(d => {
    const segs = statuses.map(s => {
      if (!d[s]) return '';
      const w = (d[s] / d.total * 100).toFixed(1);
      return `<div class="bar-segment" style="width:${w}%;background:${colors[s]}" data-tip="${labels[s]}: ${d[s]} (${w}%)"></div>`;
    }).join('');
    return `<div class="bar-row">
      <div class="bar-label">${d.label}</div>
      <div class="bar-track">${segs}</div>
      <div class="bar-meta">${d.total} tests · avg ${d.avgDur}</div>
    </div>`;
  }).join('');
  container.innerHTML = legend + `<div class="stacked-chart">${rows}</div>`;
}

let resourcesEnabled = """ + ('true' if ctx.get('res_enabled_style', 'display:none') == '' else 'false') + """;
function toggleResources() {
  resourcesEnabled = !resourcesEnabled;
  document.getElementById('res-enabled').style.display  = resourcesEnabled ? '' : 'none';
  document.getElementById('res-disabled').style.display = resourcesEnabled ? 'none' : '';
  document.getElementById('res-legend').style.display   = resourcesEnabled ? '' : 'none';
  document.getElementById('res-toggle-btn').textContent = resourcesEnabled ? 'Disable' : 'Enable';
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
  });
});

document.getElementById('global-search').addEventListener('input', applyAndRender);

/* ══ Detail panel ════════════════════════════════════════ */
function traceClass(status) {
  if (status === 'OK')   return 'ok';
  if (status === 'Fail') return 'fail';
  if (status === 'N/A')  return 'na';
  return 'bad';
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function openPanel(id) {
  const test   = TESTS.find(t => t.id === id);
  const detail = DETAILS[id];
  if (!test) return;

  document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
  const row = document.querySelector(`tr[data-id="${id}"]`);
  if (row) row.classList.add('selected');

  document.getElementById('panel-test-name').textContent = test.test + '()';
  document.getElementById('panel-suite-path').textContent =
    (detail ? detail.module + '.' : '') + test.suite + '.' + test.test;
  document.getElementById('panel-tags').innerHTML =
    (test.tags||[]).map(tag => `<span class="tag-chip">${tag}</span>`).join('');

  let html = '';
  if (detail) {
    const sm = detail.suiteMetrics || {};
    const lcKeys = { beforeClass:'@beforeClass', afterClass:'@afterClass', beforeTest:'@beforeTest', afterTest:'@afterTest' };
    html += '<div class="lifecycle-grid">';
    for (const [key, lbl] of Object.entries(lcKeys)) {
      const m = sm[key] || { avg:'—', median:'—', min:'—', max:'—', executions:0, failures:0 };
      const cardCls = m.failures > 0 ? 'lifecycle-card has-failure' : 'lifecycle-card';
      html += `<div class="${cardCls}">
        <div class="lifecycle-card-title">${lbl}${m.failures > 0 ? ' <span style="color:var(--s-error);font-size:10px">✕ failed</span>' : ''}</div>
        <div class="lifecycle-row"><span class="lifecycle-key">avg</span><span class="lifecycle-val">${m.avg}</span></div>
        <div class="lifecycle-row"><span class="lifecycle-key">median</span><span class="lifecycle-val">${m.median}</span></div>
        <div class="lifecycle-row"><span class="lifecycle-key">min / max</span><span class="lifecycle-val">${m.min} / ${m.max}</span></div>
        <div class="lifecycle-row"><span class="lifecycle-key">executions</span><span class="lifecycle-val">${m.executions > 0 ? m.executions : '<span style=\\"color:var(--ink-faint)\\">—</span>'}</span></div>
        <div class="lifecycle-row"><span class="lifecycle-key">failures</span><span class="lifecycle-val" style="color:${m.failures>0?'var(--s-error)':m.executions>0?'var(--s-success)':'var(--ink-faint)'}">${m.failures > 0 ? m.failures : m.executions > 0 ? '0' : '—'}</span></div>
      </div>`;
    }
    html += '</div>';

    const variants = detail.variants || [];
    html += `<div class="variants-title">Test Variants (${variants.length})</div>`;
    variants.forEach((v, vi) => {
      const paramLabel = v.classParam
        ? 'suite param: ' + v.classParam + (v.testParam ? ' · test param: ' + v.testParam : '')
        : (v.testParam ? 'test param: ' + v.testParam : 'No parameters');
      html += `<div class="variant-item" id="variant-${id}-${vi}">
        <div class="variant-header" onclick="toggleVariant('variant-${id}-${vi}')">
          <span class="badge badge-${v.status}">${v.status}</span>
          <span class="variant-param">${escHtml(paramLabel)}</span>
          <span class="variant-dur">${v.totalDuration}</span>
          <svg class="chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <div class="variant-body">`;
      (v.attempts || []).forEach((a, ai) => {
        const hdrExtra = `· @beforeTest <span>${a.beforeTest.status}</span> · @afterTest <span>${a.afterTest.status}</span>`;
        html += `<div class="attempt" id="attempt-${id}-${vi}-${ai}">
          <div class="attempt-header" onclick="toggleAttempt('attempt-${id}-${vi}-${ai}')">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span>Attempt ${a.n}</span> · runtime <span>${a.runtime}</span>
            ${hdrExtra}
          </div>
          <div class="attempt-body">`;
        const phases = [
          { label:'@beforeTest', data:a.beforeTest },
          { label:'@test',       data:a.test       },
          { label:'@afterTest',  data:a.afterTest  },
        ];
        phases.forEach(p => {
          const cls  = traceClass(p.data.status);
          const body = p.data.trace === 'OK' || p.data.trace === 'N/A'
            ? p.data.trace : escHtml(p.data.trace);
          html += `<div class="trace-block">
            <div class="trace-label ${cls}">${p.label} — ${p.data.status}</div>
            <div class="trace-body ${cls}">${body}</div>
            <div class="trace-runtime">${p.data.dur}</div>
          </div>`;
        });
        html += `</div></div>`;
      });
      html += `</div></div>`;
    });
  } else {
    html = `<div style="padding:20px 0;color:var(--ink-faint);font-size:13px;text-align:center">No detailed metrics for this test.</div>`;
  }

  document.getElementById('panel-body').innerHTML = html;
  document.getElementById('detail-panel').classList.add('open');
  document.getElementById('overlay').classList.add('show');
}

function toggleVariant(id) { document.getElementById(id).classList.toggle('expanded'); }
function toggleAttempt(id)  { document.getElementById(id).classList.toggle('expanded'); }
document.getElementById('panel-close').addEventListener('click', closePanel);
document.getElementById('overlay').addEventListener('click', closePanel);
function closePanel() {
  document.getElementById('detail-panel').classList.remove('open');
  document.getElementById('overlay').classList.remove('show');
  document.querySelectorAll('tbody tr').forEach(r => r.classList.remove('selected'));
}

/* ══ Support FAB ════════════════════════════════════════ */
(function() {
  const fab      = document.getElementById('support-fab');
  const backdrop = document.getElementById('support-backdrop');
  const modal    = document.getElementById('support-modal');
  const closeBtn = document.getElementById('support-close');
  function openSupport() {
    backdrop.classList.add('show');
    modal.style.display = 'block';
    requestAnimationFrame(() => modal.classList.add('show'));
  }
  function closeSupport() {
    modal.classList.remove('show');
    backdrop.classList.remove('show');
    setTimeout(() => { modal.style.display = 'none'; }, 200);
  }
  fab.addEventListener('click', openSupport);
  closeBtn.addEventListener('click', closeSupport);
  backdrop.addEventListener('click', closeSupport);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSupport(); });
})();

/* ══ Theme toggle ════════════════════════════════════════ */
document.getElementById('theme-toggle').addEventListener('click', () => {
  const isLight = document.body.classList.toggle('light');
  document.getElementById('theme-icon-dark').style.display  = isLight ? 'none' : '';
  document.getElementById('theme-icon-light').style.display = isLight ? ''     : 'none';
});

/* ══ Init ════════════════════════════════════════════════ */
const _BAR_SECTIONS = ['features','components','owners','suites','tags'];
_BAR_SECTIONS.forEach(k => renderBars('chart-' + k, BAR_DATA[k] || []));
buildFilterBar();
buildTableHead();
applyAndRender();
</script>
"""
