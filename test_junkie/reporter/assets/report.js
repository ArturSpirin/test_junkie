
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
let tracebackFilterIds = null;

function applyTracebackFilter(idsArr) {
  tracebackFilterIds = new Set(idsArr.map(Number));
  document.getElementById('tb-filter-strip').classList.add('visible');
  applyAndRender();
}
function clearTracebackFilter() {
  tracebackFilterIds = null;
  document.getElementById('tb-filter-strip').classList.remove('visible');
  applyAndRender();
}

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
  clearTracebackFilter();
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
    if (tracebackFilterIds !== null && !tracebackFilterIds.has(t.id)) return false;
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
      if (typeof val === 'string') val = escHtml(val);  // names/owners/etc come from user code
      if (col.key === 'test' && t.variantCount > 1) {
        val = `${val}<span class="variant-count-chip">⊞ ×${t.variantCount}</span>`;
      } else if (col.key === 'tags') {
        const MAX = 1;
        const visible = (t.tags||[]).slice(0, MAX);
        const extra = (t.tags||[]).length - MAX;
        const chips = visible.map(tag => `<span class="tag-chip">${escHtml(tag)}</span>`).join('');
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

let resourcesEnabled = RESOURCES_ENABLED;
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
    (test.tags||[]).map(tag => `<span class="tag-chip">${escHtml(tag)}</span>`).join('');

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
        <div class="lifecycle-row"><span class="lifecycle-key">executions</span><span class="lifecycle-val">${m.executions > 0 ? m.executions : '<span style=\"color:var(--ink-faint)\">—</span>'}</span></div>
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
        const retryNote = a.retry ? ` · retried (${escHtml(a.retry.policy)}, when ${escHtml(a.retry.when)}${a.retry.waited ? ', waited ' + a.retry.waited + 's' : ''})` : '';
        const hdrExtra = `· @beforeTest <span>${a.beforeTest.status}</span> · @afterTest <span>${a.afterTest.status}</span>${retryNote}`;
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

/* ══ Threading dialog ════════════════════════════════════ */
function openThreadingDialog() {
  if (!THREADING_DATA) return;
  const d = THREADING_DATA;
  const sum = document.getElementById('td-summary');
  sum.innerHTML = `
    <div class="td-metric">
      <div class="td-metric-label">Current (sequential)</div>
      <div class="td-metric-value">${d.serial_time}s</div>
      <div class="td-metric-sub">${d.test_count} tests · 1 thread</div>
    </div>
    <div class="td-metric highlight">
      <div class="td-metric-label">Recommended (${d.recommended_threads} threads)</div>
      <div class="td-metric-value">~${d.estimated_time}s</div>
      <div class="td-metric-sub">${d.speedup}× faster · saves ~${d.time_saved}s per run</div>
    </div>`;
  document.getElementById('td-code').textContent =
    `Runner(..., test_multithreading_limit=${d.recommended_threads})`;
  const tbody = document.getElementById('td-tbody');
  const maxDur = d.top_tests[0] ? d.top_tests[0].dur : 1;
  tbody.innerHTML = d.top_tests.map((t, i) => {
    const barW = Math.round(t.dur / maxDur * 80);
    return `<tr>
      <td><span class="rank-bar" style="width:${barW}px"></span>${escHtml(t.name)}</td>
      <td style="color:var(--ink-faint)">${escHtml(t.suite)}</td>
      <td class="dur-cell">${t.dur.toFixed(3)}s</td>
    </tr>`;
  }).join('');
  const bottleneck = d.top_tests[0] ? d.top_tests[0].dur.toFixed(3) + 's' : '—';
  document.getElementById('td-note').innerHTML =
    `The minimum possible parallel run time is bounded by the slowest test: <strong style="color:var(--ink)">${bottleneck}</strong>. ` +
    `Tests marked <code>parallelized=False</code> run in isolation and are excluded from threading gains. ` +
    `Thread count above ${d.recommended_threads} shows diminishing returns for this test suite.`;
  document.getElementById('thread-backdrop').style.display = 'block';
  document.getElementById('thread-dialog').style.display = 'block';
  document.body.style.overflow = 'hidden';
}
function closeThreadingDialog() {
  document.getElementById('thread-backdrop').style.display = 'none';
  document.getElementById('thread-dialog').style.display = 'none';
  document.body.style.overflow = '';
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeThreadingDialog(); });

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
