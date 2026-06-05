/* ═══════════════════════════════════════════════════════
   FACTORIO OPTIMIZER — app.js
   Full interactive UI: item picker, modules, optimizer,
   chain tree, energy view, compare table
   ═══════════════════════════════════════════════════════ */

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  items: {},          // { early: [...], mid: [...], end: [...] }
  modules: {},        // { mid: [...], end: [...] }
  selectedItem: null,
  selectedEra: 'early',
  machineEra: 'mid',
  useElectricFurnace: false,
  moduleStates: {},   // { module_name: count }
  lastResult: null,
  activeResultTab: 'best',
  energyView: 'steam',  // 'steam' | 'solar'
};

// ── Init ───────────────────────────────────────────────────────────────────
async function init() {
  await Promise.all([loadItems(), loadModules()]);
  renderItemList();
  renderModuleGrid();
}

// ── Data loading ───────────────────────────────────────────────────────────
async function loadItems() {
  try {
    const res = await fetch('/api/items');
    state.items = await res.json();
  } catch (e) {
    document.getElementById('item-list').innerHTML =
      '<div class="loading-spinner">❌ Failed to load items</div>';
  }
}

async function loadModules() {
  try {
    const res = await fetch('/api/modules');
    state.modules = await res.json();
  } catch (e) {
    document.getElementById('module-grid').innerHTML =
      '<div class="loading-spinner">❌ Failed to load modules</div>';
  }
}

// ── Item list ──────────────────────────────────────────────────────────────
function renderItemList(filter = '') {
  const container = document.getElementById('item-list');
  
  let itemsToSearch = [];
  const eraTabs = document.querySelector('.era-tabs');
  
  if (filter) {
    itemsToSearch = [
      ...(state.items.early || []), 
      ...(state.items.mid || []), 
      ...(state.items.end || [])
    ];
    if (eraTabs) eraTabs.style.display = 'none';
  } else {
    const era = state.selectedEra;
    itemsToSearch = state.items[era] || [];
    if (eraTabs) eraTabs.style.display = 'flex';
  }

  const filtered = filter
    ? itemsToSearch.filter(i => i.display_name.toLowerCase().includes(filter.toLowerCase()))
    : itemsToSearch;

  if (!filtered.length) {
    container.innerHTML = '<div class="loading-spinner">No items found</div>';
    return;
  }

  // Group by category
  const groups = {};
  for (const item of filtered) {
    const cat = item.category || 'other';
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(item);
  }

  const catOrder = ['science', 'intermediate', 'logistics', 'military', 'raw', 'other'];
  const catIcons = {
    science: '🔬', intermediate: '⚙️', logistics: '📦',
    military: '⚔️', raw: '⛏️', other: '📦',
  };

  let html = '';
  for (const cat of catOrder) {
    if (!groups[cat]) continue;
    html += `<div class="item-category-label">${catIcons[cat] || '📦'} ${cat}</div>`;
    for (const item of groups[cat]) {
      const sel = state.selectedItem?.name === item.name ? 'selected' : '';
      html += `
        <button class="item-btn ${sel}" onclick="selectItemByName('${item.name}')"
                id="itembtn-${item.name}" title="${item.display_name}">
          <span class="item-icon">${item.icon}</span>
          <span class="item-name">${item.display_name}</span>
          <span class="item-cat-badge">${cat}</span>
        </button>`;
    }
  }

  container.innerHTML = html;
}

function selectItemByName(name) {
  let found = null;
  for (const era of ['early', 'mid', 'end']) {
    if (state.items[era]) {
      found = state.items[era].find(i => i.name === name);
      if (found) break;
    }
  }
  if (found) selectItem(found);
}

function selectItem(item) {
  state.selectedItem = item;

  // Update UI
  document.querySelectorAll('.item-btn').forEach(b => b.classList.remove('selected'));
  const btn = document.getElementById(`itembtn-${item.name}`);
  if (btn) btn.classList.add('selected');

  document.getElementById('sel-icon').textContent = item.icon;
  document.getElementById('sel-name').textContent = item.display_name;
  document.getElementById('sel-sub').textContent = `${item.category} · ${item.era} game`;

  const optimizeBtn = document.getElementById('optimize-btn');
  optimizeBtn.disabled = false;
  document.getElementById('optimize-btn-text').textContent =
    `Optimize — ${item.display_name}`;
}

// ── Era tabs (item picker) ─────────────────────────────────────────────────
document.querySelectorAll('.era-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.era-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    state.selectedEra = tab.dataset.era;
    
    if (state.selectedEra === 'saved') {
      document.getElementById('item-list').style.display = 'none';
      document.getElementById('saved-list').style.display = 'block';
    } else {
      document.getElementById('item-list').style.display = 'block';
      document.getElementById('saved-list').style.display = 'none';
      renderItemList(document.getElementById('item-search').value);
    }
  });
});

document.getElementById('item-search').addEventListener('input', e => {
  renderItemList(e.target.value);
});

// ── Machine tier ───────────────────────────────────────────────────────────
document.querySelectorAll('.tier-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tier-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.machineEra = btn.dataset.era;
    updateFurnaceSection();
  });
});

function updateFurnaceSection() {
  const section = document.getElementById('furnace-section');
  section.style.display = state.machineEra === 'early' ? 'none' : '';
}

function setFurnace(electric) {
  state.useElectricFurnace = electric;
  document.getElementById('furnace-steel').classList.toggle('active', !electric);
  document.getElementById('furnace-electric').classList.toggle('active', electric);
}

// ── Module grid ────────────────────────────────────────────────────────────
function renderModuleGrid() {
  const grid = document.getElementById('module-grid');

  // Collect mid-game modules (always show in mid-game UI)
  const mods = [
    ...(state.modules.mid || []),
    ...(state.modules.end || []),
  ];

  if (!mods.length) {
    grid.innerHTML = '<div class="loading-spinner">No modules available</div>';
    return;
  }

  let html = '';
  for (const mod of mods) {
    const typeClass = `selected-${mod.module_type}`;
    const chipClass = `chip-${mod.module_type}`;
    const isSel = (state.moduleStates[mod.name] || 0) > 0;

    const stats = buildModuleStatBadges(mod);

    html += `
      <div class="module-card ${isSel ? typeClass : ''}"
           id="modcard-${mod.name}"
           onclick="toggleModule('${mod.name}', '${mod.module_type}')">
        <div class="module-card-name">${mod.display_name}</div>
        <div class="module-card-stats">${stats}</div>
        <div class="module-count-ctrl" onclick="event.stopPropagation()">
          <button class="count-btn" onclick="changeModuleCount('${mod.name}', '${mod.module_type}', -1)">−</button>
          <span class="count-val" id="mcount-${mod.name}">${state.moduleStates[mod.name] || 0}</span>
          <button class="count-btn" onclick="changeModuleCount('${mod.name}', '${mod.module_type}', +1)">+</button>
        </div>
      </div>`;
  }

  grid.innerHTML = html;
}

function buildModuleStatBadges(mod) {
  let html = '';
  if (mod.speed_bonus_pct !== 0) {
    const cls = mod.speed_bonus_pct > 0 ? 'pos' : 'neg';
    html += `<span class="mod-stat ${cls}">⚡ ${mod.speed_bonus_pct > 0 ? '+' : ''}${mod.speed_bonus_pct}%</span>`;
  }
  if (mod.productivity_bonus_pct !== 0) {
    const cls = mod.productivity_bonus_pct > 0 ? 'pos' : 'neg';
    html += `<span class="mod-stat ${cls}">📈 ${mod.productivity_bonus_pct > 0 ? '+' : ''}${mod.productivity_bonus_pct}%</span>`;
  }
  if (mod.energy_bonus_pct !== 0) {
    const cls = mod.energy_bonus_pct < 0 ? 'pos' : 'neg';
    html += `<span class="mod-stat ${cls}">🔋 ${mod.energy_bonus_pct > 0 ? '+' : ''}${mod.energy_bonus_pct}%</span>`;
  }
  return html;
}

function toggleModule(name, type) {
  const cur = state.moduleStates[name] || 0;
  if (cur === 0) {
    state.moduleStates[name] = 1;
  } else {
    state.moduleStates[name] = 0;
  }
  updateModuleCardUI(name, type);
  updateActiveModulesBar();
}

function changeModuleCount(name, type, delta) {
  const cur = state.moduleStates[name] || 0;
  const next = Math.max(0, Math.min(4, cur + delta));
  state.moduleStates[name] = next;
  updateModuleCardUI(name, type);
  updateActiveModulesBar();
}

function updateModuleCardUI(name, type) {
  const card = document.getElementById(`modcard-${name}`);
  const countEl = document.getElementById(`mcount-${name}`);
  const count = state.moduleStates[name] || 0;

  if (card) {
    card.classList.remove('selected-speed', 'selected-productivity', 'selected-efficiency');
    if (count > 0) card.classList.add(`selected-${type}`);
  }
  if (countEl) countEl.textContent = count;
}

function updateActiveModulesBar() {
  const bar = document.getElementById('active-modules');
  const active = Object.entries(state.moduleStates).filter(([, v]) => v > 0);

  if (!active.length) {
    bar.innerHTML = '<span class="no-modules-note">No modules selected — click to add</span>';
    return;
  }

  // Find module info from loaded modules
  const allMods = [...(state.modules.mid || []), ...(state.modules.end || [])];
  const modMap = Object.fromEntries(allMods.map(m => [m.name, m]));

  const chips = active.map(([name, count]) => {
    const mod = modMap[name];
    if (!mod) return '';
    return `<span class="active-mod-chip chip-${mod.module_type}">
      ${mod.display_name} ×${count}
    </span>`;
  }).join('');

  bar.innerHTML = chips;
}

function getModuleConfigs() {
  return Object.entries(state.moduleStates)
    .filter(([, count]) => count > 0)
    .map(([name, count]) => ({ name, count }));
}

// ── Optimize ───────────────────────────────────────────────────────────────
async function runOptimize() {
  if (!state.selectedItem) return;

  const rate = parseFloat(document.getElementById('rate-input').value) || 1;
  const unit = document.getElementById('rate-unit').value;

  const body = {
    item: state.selectedItem.name,
    rate,
    unit,
    era: state.machineEra,
    use_electric_furnace: state.useElectricFurnace,
    modules: getModuleConfigs(),
  };

  // Show loading
  setResultsState('loading');

  const btn = document.getElementById('optimize-btn');
  btn.classList.add('loading');
  btn.disabled = true;
  document.getElementById('optimize-btn-text').textContent = 'Solving…';

  try {
    const res = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    state.lastResult = data;
    renderResults(data);

  } catch (err) {
    setResultsState('placeholder');
    alert(`Optimization failed: ${err.message}`);
  } finally {
    btn.classList.remove('loading');
    btn.disabled = false;
    document.getElementById('optimize-btn-text').textContent =
      `Optimize — ${state.selectedItem.display_name}`;
  }
}

// ── Results rendering ──────────────────────────────────────────────────────
async function runSelectedMidBlock() {
  if (!state.selectedItem) {
    alert('Select a mid-tier item first.');
    return;
  }
  await runMilestoneGenerator('/api/generate-mid-tier-slice', `${state.selectedItem.display_name} Slice`, {
    item: state.selectedItem.name,
    strategy: 'readable',
  });
}

async function runScaledEarlySciencePlanner() {
  const rate = parseFloat(document.getElementById('rate-input').value) || 300;
  const unit = document.getElementById('rate-unit').value;
  const targetPerMinute = unit === 'per_second' ? rate * 60 : rate;
  const blockRate = targetPerMinute >= 120 ? 30 : 15;

  await runMilestoneGenerator(
    '/api/generate-scaled-early-science-plan',
    `Scaled Early Science Plan (${targetPerMinute.toFixed(0)}/min)`,
    {
      block_rate: blockRate,
      block_unit: 'per_minute',
    },
  );
}

async function runMilestoneGenerator(endpoint, label, extraBody = {}) {
  const rate = parseFloat(document.getElementById('rate-input').value) || 30;
  const unit = document.getElementById('rate-unit').value;
  const body = {
    rate,
    unit,
    machine_tier: state.machineEra === 'early' ? 'early' : 'mid',
    transport_tier: state.machineEra === 'early' ? 'early' : 'mid',
    fluid_mode: 'external',
    ...extraBody,
  };

  setResultsState('loading');
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    state.lastResult = data;
    renderBlueprintReport(label, data);
  } catch (err) {
    setResultsState('placeholder');
    alert(`Blueprint generation failed: ${err.message}`);
  }
}

function renderBlueprintReport(label, data) {
  setResultsState('results');
  state.activeResultTab = 'best';
  updateResultTabButtons();

  const summary = data.summary || {};
  const diagnostics = data.diagnostics || {};
  const warnings = diagnostics.warnings || [];
  const externalInputs = Object.keys(diagnostics.external_inputs || {});
  const laneGuideHtml = renderLaneGuide(diagnostics);
  const buildSummaryHtml = renderBlueprintBuildSummary(data.build_list || {});
  const scaledPlanHtml = renderScaledPlanGuide(summary, diagnostics);
  const machineLabel = typeof summary.block_count === 'number' ? 'Assemblers / Labs' : 'Machines';

  document.getElementById('summary-cards').innerHTML = `
    <div class="summary-card ${data.valid ? 'card-green' : 'card-purple'}">
      <div class="sc-icon">${data.valid ? 'OK' : '!'}</div>
      <div class="sc-value">${data.valid ? 'Valid' : 'Check'}</div>
      <div class="sc-label">Blueprint Confidence</div>
    </div>
    <div class="summary-card card-blue">
      <div class="sc-icon">CAP</div>
      <div class="sc-value">${(summary.capacity_per_minute || 0).toFixed(1)}/min</div>
      <div class="sc-label">Capacity</div>
    </div>
    <div class="summary-card card-amber">
      <div class="sc-icon">ASM</div>
      <div class="sc-value">${summary.machine_count || 0}</div>
      <div class="sc-label">${machineLabel}</div>
    </div>`;

  document.getElementById('chain-tree').innerHTML = `
    <div class="energy-card">
      <div class="energy-card-title">${escapeHtml(label)}</div>
      <div class="energy-row">
        <span class="energy-row-label">External inputs</span>
        <span class="energy-row-val">${externalInputs.length ? externalInputs.join(', ') : 'none'}</span>
      </div>
      <div class="energy-row">
        <span class="energy-row-label">Warnings</span>
        <span class="energy-row-val">${warnings.length ? warnings.join('; ') : 'none'}</span>
      </div>
      <button class="save-layout-btn" onclick="copyBlueprintString()">Copy Blueprint String</button>
      <span id="blueprint-copy-status" class="blueprint-copy-status">Ready to copy</span>
      <textarea
        id="blueprint-string-output"
        class="blueprint-string-output"
        readonly
        spellcheck="false"
        onclick="this.select()"
      >${escapeHtml(data.blueprint_string || '')}</textarea>
      ${buildSummaryHtml}
      ${scaledPlanHtml}
      ${laneGuideHtml}
      <pre class="ascii-preview">${escapeHtml(data.ascii || '')}</pre>
    </div>`;
  document.getElementById('compare-table').innerHTML = '<div class="loading-spinner">Blueprint generator reports do not include plan comparison yet.</div>';
  document.getElementById('energy-view').innerHTML = `<pre class="ascii-preview">${escapeHtml(JSON.stringify(data.validation_confidence || {}, null, 2))}</pre>`;
  document.getElementById('raw-inputs-view').innerHTML = laneGuideHtml || `<pre class="ascii-preview">${escapeHtml(JSON.stringify(diagnostics.external_inputs || {}, null, 2))}</pre>`;
  showResultTab('best');
}

function renderScaledPlanGuide(summary, diagnostics) {
  const sections = Array.isArray(diagnostics.sections) ? diagnostics.sections : [];
  if (!sections.length) return '';

  const trainReadiness = diagnostics.train_readiness || {};
  const blockCount = summary.block_count || sections.length;
  const blockRate = summary.block_rate_per_minute || sections[0]?.target_per_minute || 0;
  const sectionRows = sections.map((section, index) => `
    <div class="scaled-plan-row">
      <div>
        <div class="scaled-plan-item">${escapeHtml(section.name || `Section ${index + 1}`)}</div>
        <div class="scaled-plan-note">Paste the representative blueprint once here. Target ${Number(section.target_per_minute || 0).toFixed(1)}/min.</div>
      </div>
      <span class="scaled-plan-rate">#${index + 1}</span>
    </div>
  `).join('');

  const stationRows = (trainReadiness.station_blocks || []).map((station) => `
    <div class="scaled-plan-row scaled-plan-row-station">
      <div>
        <div class="scaled-plan-item">${escapeHtml(formatItemName(station.item))} unload</div>
        <div class="scaled-plan-note">${escapeHtml(station.notes || '')}</div>
      </div>
      <span class="scaled-plan-rate">${escapeHtml(String(station.minimum_output_belts || 1))} belt(s)</span>
    </div>
  `).join('');

  return `
    <details class="scaled-plan-guide" open>
      <summary>
        <span>Repeatable Paste Plan</span>
        <span class="build-summary-meta">${blockCount} blocks at ${Number(blockRate).toFixed(1)}/min each</span>
      </summary>
      <div class="scaled-plan-body">
        <div class="scaled-plan-intro">
          Use the blueprint string above as the representative block. Paste it ${blockCount} times in a row, keeping the same lane orientation.
        </div>
        <div class="scaled-plan-section-label">Sections</div>
        ${sectionRows}
        <div class="scaled-plan-section-label">Transport Readiness</div>
        <div class="scaled-plan-intro">${escapeHtml(trainReadiness.reason || 'Belts are sufficient for this target rate.')}</div>
        ${stationRows || '<div class="scaled-plan-empty">No train unload stations needed yet for this target.</div>'}
      </div>
    </details>`;
}

function renderBlueprintBuildSummary(buildList) {
  const entries = Object.entries(buildList)
    .filter(([, count]) => typeof count === 'number' && count > 0)
    .sort((a, b) => b[1] - a[1]);
  if (!entries.length) return '';

  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  const chips = entries.map(([name, count]) => `
    <span class="blueprint-build-chip">
      <span>${escapeHtml(formatBuildName(name))}</span>
      <strong>×${Number(count || 0)}</strong>
    </span>
  `).join('');

  return `
    <details class="blueprint-build-summary" open>
      <summary>
        <span>Build Summary</span>
        <span class="build-summary-meta">${total} total entities</span>
      </summary>
      <div class="blueprint-build-chip-row">${chips}</div>
    </details>`;
}

function formatBuildName(name) {
  return String(name)
    .replace(/s$/, '')
    .replaceAll('_', ' ');
}

function renderLaneGuide(diagnostics) {
  const inputLanes = diagnostics.external_input_lanes || {};
  const outputLanes = diagnostics.output_lanes || {};
  const rates = diagnostics.external_inputs || {};
  const inputRows = Object.entries(inputLanes).map(([item, points]) => {
    const rate = rates[item];
    const rateText = typeof rate === 'number' ? `${rate.toFixed(3)}/s` : 'see upstream';
    const pointText = formatLanePoints(points);
    return `
      <div class="lane-row">
        <div>
          <div class="lane-item">${escapeHtml(formatItemName(item))}</div>
          <div class="lane-note">${escapeHtml(pointText)}</div>
        </div>
        <span class="lane-rate">${escapeHtml(rateText)}</span>
      </div>`;
  }).join('');
  const outputRows = Object.entries(outputLanes).map(([item, lane]) => `
    <div class="lane-row lane-output">
      <div>
        <div class="lane-item">${escapeHtml(formatItemName(item))}</div>
        <div class="lane-note">${escapeHtml(formatOutputLane(lane))}</div>
      </div>
      <span class="lane-rate">output</span>
    </div>`).join('');
  if (!inputRows && !outputRows) return '';
  return `
    <div class="lane-guide">
      <div class="energy-card-title">Feed / Output Lane Guide</div>
      ${inputRows ? `<div class="lane-section-label">Inputs</div>${inputRows}` : ''}
      ${outputRows ? `<div class="lane-section-label">Outputs</div>${outputRows}` : ''}
    </div>`;
}

function formatLanePoints(points) {
  if (!Array.isArray(points)) return 'no coordinate data';
  return points.map(point => {
    if (point.pattern) return point.pattern;
    if (typeof point.x === 'number' && typeof point.y === 'number') return `tile (${point.x}, ${point.y})`;
    return JSON.stringify(point);
  }).join(', ');
}

function formatOutputLane(lane) {
  const parts = [];
  if (lane.main_bus_start) parts.push(`starts at (${lane.main_bus_start.x}, ${lane.main_bus_start.y})`);
  if (lane.feeds_lab) parts.push('feeds lab');
  if (lane.exits_right) parts.push('exits right');
  return parts.join(' · ') || 'output lane';
}

function formatItemName(item) {
  return String(item).replaceAll('_', ' ');
}

async function copyBlueprintString() {
  const box = document.getElementById('blueprint-string-output');
  const status = document.getElementById('blueprint-copy-status');
  const blueprint = state.lastResult?.blueprint_string || box?.value || '';

  if (!blueprint) {
    if (status) status.textContent = 'No blueprint string available.';
    return;
  }

  try {
    await navigator.clipboard.writeText(blueprint);
    if (status) status.textContent = 'Copied.';
    showToast();
  } catch (_err) {
    if (box) {
      box.focus();
      box.select();
      if (status) status.textContent = 'Clipboard blocked. Press Ctrl+C now.';
      return;
    }
    if (status) status.textContent = 'Clipboard blocked.';
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function setResultsState(state) {
  document.getElementById('results-placeholder').style.display = state === 'placeholder' ? '' : 'none';
  document.getElementById('results-loading').style.display = state === 'loading' ? '' : 'none';
  document.getElementById('tab-best').style.display = 'none';
  document.getElementById('tab-compare').style.display = 'none';
  document.getElementById('tab-energy').style.display = 'none';
  document.getElementById('tab-raw').style.display = 'none';
  document.getElementById('results-tabs').style.display = state === 'results' ? '' : 'none';
}

function renderResults(data) {
  setResultsState('results');
  state.activeResultTab = 'best';
  updateResultTabButtons();

  const best = data.plans[0];

  // ── Summary cards ──
  renderSummaryCards(best, data);

  // ── Chain tree ──
  renderChainTree(best.chain);

  // ── Compare table ──
  renderCompareTable(data.plans);

  // ── Energy view ──
  renderEnergyView(best.energy_plan);

  // ── Raw inputs ──
  renderRawInputs(best.raw_inputs);

  // Show best tab
  showResultTab('best');
}

function renderSummaryCards(best, data) {
  const uptimeColor = best.avg_uptime_pct >= 90 ? 'green' : best.avg_uptime_pct >= 75 ? 'amber' : 'card-purple';
  const html = `
    <div class="summary-card card-green">
      <div class="sc-icon">⏱️</div>
      <div class="sc-value">${best.avg_uptime_pct}%</div>
      <div class="sc-label">Avg Uptime</div>
    </div>
    <div class="summary-card card-amber">
      <div class="sc-icon">🏭</div>
      <div class="sc-value">${best.total_machines}</div>
      <div class="sc-label">Total Machines</div>
    </div>
    <div class="summary-card card-blue">
      <div class="sc-icon">⚡</div>
      <div class="sc-value">${formatKw(best.total_energy_kw)}</div>
      <div class="sc-label">Power Draw</div>
    </div>
    <div class="summary-card card-purple">
      <div class="sc-icon">🎯</div>
      <div class="sc-value">${best.score}</div>
      <div class="sc-label">Efficiency Score</div>
    </div>`;
  document.getElementById('summary-cards').innerHTML = html;
}

function formatKw(kw) {
  if (kw >= 1000) return (kw / 1000).toFixed(2) + ' MW';
  return kw.toFixed(0) + ' kW';
}

// ── Chain tree ─────────────────────────────────────────────────────────────
function renderChainTree(node, depth = 0) {
  const container = document.getElementById('chain-tree');
  if (depth === 0) container.innerHTML = '';

  const nodeEl = buildChainNodeEl(node, depth);
  if (depth === 0) {
    container.appendChild(nodeEl);
  }
  return nodeEl;
}

function buildChainNodeEl(node, depth) {
  const div = document.createElement('div');
  div.className = `chain-node${node.is_raw ? ' is-raw' : ''}`;
  div.style.animationDelay = `${depth * 0.06}s`;

  if (node.is_raw) {
    div.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">${node.icon}</span>
        <div class="cn-info">
          <div class="cn-name">${node.display_name}
            <span class="cn-raw-badge">raw resource</span>
          </div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">— miners</span>
          <span class="cn-rate">${node.target_per_second.toFixed(3)}/s</span>
        </div>
      </div>`;
    return div;
  }

  const uptimePct = node.uptime_pct;
  const uptimeClass = uptimePct >= 90 ? 'good' : uptimePct >= 70 ? 'mid' : 'poor';
  
  const isBlackbox = node.is_blackbox;
  const blackboxBadge = isBlackbox ? '<span class="cn-raw-badge" style="background:var(--amber-dim); color:var(--amber);">📦 Modular Blueprint</span>' : '';
  const nodeClass = `chain-node${isBlackbox ? ' is-blackbox' : ''}`;

  div.className = nodeClass;
  div.innerHTML = `
    <div class="chain-node-header" onclick="toggleChildren('${node.item}')">
      <span class="cn-icon">${node.icon}</span>
      <div class="cn-info">
        <div class="cn-name">${node.display_name} ${blackboxBadge}</div>
        <div class="cn-machine">🏭 ${node.machine_display_name}</div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">×${node.machine_count_ceil}</span>
        <span class="cn-rate">${node.target_per_minute.toFixed(1)}/min</span>
      </div>
    </div>
    <div class="uptime-bar-wrap">
      <div class="uptime-label-row">
        <span>Machine uptime</span>
        <span class="uptime-pct-text ${uptimeClass}">${uptimePct.toFixed(1)}%</span>
      </div>
      <div class="uptime-track">
        <div class="uptime-fill ${uptimeClass}" id="bar-${node.item}" style="width:0%"></div>
      </div>
    </div>
    <div class="cn-energy">
      ⚡ <span>${node.effective_power_kw.toFixed(0)} kW</span>
      &nbsp;·&nbsp; exact: ${node.machine_count_exact.toFixed(2)} machines
      ${node.productivity_bonus_pct ? `&nbsp;·&nbsp; 📈 +${node.productivity_bonus_pct}% prod` : ''}
      ${node.speed_bonus_pct ? `&nbsp;·&nbsp; ⚡ +${node.speed_bonus_pct}% speed` : ''}
    </div>
    ${(!isBlackbox && node.children && node.children.length) ? `<div class="chain-children" id="ch-${node.item}"></div>` : ''}`;

  // Animate uptime bar after paint
  requestAnimationFrame(() => {
    setTimeout(() => {
      const bar = div.querySelector(`#bar-${node.item}`);
      if (bar) bar.style.width = `${uptimePct}%`;
    }, 80 + depth * 60);
  });

  // Recursively build children
  if (node.children.length) {
    const childContainer = div.querySelector(`#ch-${node.item}`);
    if (childContainer) {
      for (const child of node.children) {
        childContainer.appendChild(buildChainNodeEl(child, depth + 1));
      }
    }
  }

  return div;
}

function toggleChildren(item) {
  const ch = document.getElementById(`ch-${item}`);
  if (!ch) return;
  ch.style.display = ch.style.display === 'none' ? '' : 'none';
}

// ── Compare table ──────────────────────────────────────────────────────────
function renderCompareTable(plans) {
  const el = document.getElementById('compare-table');
  let html = `
    <table class="compare-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Configuration</th>
          <th>Score</th>
          <th>Uptime</th>
          <th>Machines</th>
          <th>Energy</th>
          <th>kW/output</th>
        </tr>
      </thead>
      <tbody>`;

  plans.forEach((plan, i) => {
    const isBest = i === 0;
    html += `
      <tr class="${isBest ? 'best-plan' : ''}">
        <td>${i + 1}</td>
        <td class="plan-name">
          ${plan.name}
          ${isBest ? '<span class="best-badge">Best</span>' : ''}
        </td>
        <td><span class="score-badge">${plan.score}</span></td>
        <td>${plan.avg_uptime_pct}%</td>
        <td>${plan.total_machines}</td>
        <td>${formatKw(plan.total_energy_kw)}</td>
        <td>${plan.energy_kw_per_output} kW</td>
      </tr>`;
  });

  html += '</tbody></table>';
  el.innerHTML = html;
}

// ── Energy view ────────────────────────────────────────────────────────────
function renderEnergyView(ep) {
  const el = document.getElementById('energy-view');
  el.innerHTML = `
    <div class="energy-toggle-row">
      <button class="e-toggle-btn active" id="etog-steam" onclick="switchEnergyView('steam')">
        🔥 Steam Setup
      </button>
      <button class="e-toggle-btn" id="etog-solar" onclick="switchEnergyView('solar')">
        ☀️ Solar Setup
      </button>
    </div>
    <div class="energy-card">
      <div class="energy-total-kw">${formatKw(ep.total_demand_kw)}</div>
      <div class="energy-total-label">Total factory power demand</div>
    </div>
    <div id="energy-setup-card"></div>`;

  renderEnergySetupCard(ep, 'steam');
  window._lastEnergyPlan = ep;
}

function switchEnergyView(type) {
  state.energyView = type;
  document.getElementById('etog-steam').classList.toggle('active', type === 'steam');
  document.getElementById('etog-solar').classList.toggle('active', type === 'solar');
  renderEnergySetupCard(window._lastEnergyPlan, type);
}

function renderEnergySetupCard(ep, type) {
  const el = document.getElementById('energy-setup-card');
  if (!ep || !el) return;

  if (type === 'steam') {
    const s = ep.steam;
    el.innerHTML = `
      <div class="energy-card">
        <div class="energy-card-title">🔥 Steam Power Setup</div>
        <div class="energy-row">
          <span class="energy-row-label">🪨 Boilers</span>
          <span class="energy-row-val">${s.boilers}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">⚙️ Steam Engines</span>
          <span class="energy-row-val">${s.steam_engines}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">📊 Installed Capacity</span>
          <span class="energy-row-val">${formatKw(s.capacity_kw)}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">🛡️ Headroom</span>
          <span class="energy-row-val">${s.headroom_pct}%</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">⚡ Efficiency</span>
          <span class="energy-row-val">${ep.kw_per_output} kW / item·s</span>
        </div>
      </div>`;
  } else {
    const sol = ep.solar;
    el.innerHTML = `
      <div class="energy-card">
        <div class="energy-card-title">☀️ Solar Power Setup</div>
        <div class="energy-row">
          <span class="energy-row-label">☀️ Solar Panels</span>
          <span class="energy-row-val">${sol.solar_panels}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">🔋 Accumulators</span>
          <span class="energy-row-val">${sol.accumulators}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">📊 Peak Capacity</span>
          <span class="energy-row-val">${formatKw(sol.peak_capacity_kw)}</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">💾 Night Storage</span>
          <span class="energy-row-val">${sol.stored_mj.toFixed(0)} MJ</span>
        </div>
        <div class="energy-row">
          <span class="energy-row-label">⚡ Efficiency</span>
          <span class="energy-row-val">${ep.kw_per_output} kW / item·s</span>
        </div>
      </div>`;
  }
}

// ── Raw inputs ─────────────────────────────────────────────────────────────
function renderRawInputs(rawInputs) {
  const el = document.getElementById('raw-inputs-view');
  const allItems = { ...state.items.early, ...state.items.mid, ...state.items.end };

  // Build icon map from flat item list
  const iconMap = {};
  const nameMap = {};
  for (const era of ['early', 'mid', 'end']) {
    for (const item of (state.items[era] || [])) {
      iconMap[item.name] = item.icon;
      nameMap[item.name] = item.display_name;
    }
  }

  const rawIcons = {
    iron_ore: '🪨', copper_ore: '🟠', coal: '⬛', stone: '🪨',
    water: '💧', crude_oil: '🛢️', wood: '🪵',
    petroleum_gas: '💨', heavy_oil: '🫙', light_oil: '💛', lubricant: '🟡',
  };

  const sorted = Object.entries(rawInputs).sort((a, b) => b[1] - a[1]);

  let html = '<div class="raw-inputs-grid">';
  sorted.forEach(([item, rate], i) => {
    const icon = rawIcons[item] || iconMap[item] || '⛏️';
    const name = nameMap[item] || item.replace(/_/g, ' ');
    const rateMin = (rate * 60).toFixed(2);
    html += `
      <div class="raw-input-row" style="animation-delay:${i * 0.05}s">
        <span class="raw-icon">${icon}</span>
        <span class="raw-name">${name}</span>
        <div>
          <div class="raw-rate">${rate.toFixed(4)}/s</div>
          <div class="raw-rate-min">${rateMin}/min</div>
        </div>
      </div>`;
  });
  html += '</div>';
  el.innerHTML = html;
}

// ── Result tab switching ───────────────────────────────────────────────────
function showResultTab(tab) {
  state.activeResultTab = tab;
  updateResultTabButtons();

  document.getElementById('tab-best').style.display    = tab === 'best'    ? '' : 'none';
  document.getElementById('tab-compare').style.display = tab === 'compare' ? '' : 'none';
  document.getElementById('tab-energy').style.display  = tab === 'energy'  ? '' : 'none';
  document.getElementById('tab-raw').style.display     = tab === 'raw'     ? '' : 'none';
}

function updateResultTabButtons() {
  const tabs = ['best', 'compare', 'energy', 'raw'];
  tabs.forEach(t => {
    const btn = document.getElementById(`rtab-${t}`);
    if (btn) btn.classList.toggle('active', t === state.activeResultTab);
  });
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast() {
  const toast = document.getElementById('toast');
  toast.style.display = '';
  setTimeout(() => { toast.style.display = 'none'; }, 2600);
}

// ── Keyboard shortcut ──────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    const btn = document.getElementById('optimize-btn');
    if (!btn.disabled) runOptimize();
  }
});

// ── Saved Layouts ──────────────────────────────────────────────────────────

async function loadSavedLayouts() {
  try {
    const res = await fetch('/api/layouts');
    state.savedLayouts = await res.json();
    renderSavedLayouts();
  } catch (e) {
    console.error('Failed to load saved layouts', e);
  }
}

function renderSavedLayouts() {
  const container = document.getElementById('saved-list');
  if (!state.savedLayouts || !state.savedLayouts.length) {
    container.innerHTML = '<div class="loading-spinner">No saved layouts yet. Optimize a factory and click "Save to Favorites".</div>';
    return;
  }

  let html = '';
  for (const layout of state.savedLayouts) {
    const plan = layout.plan_data;
    const date = new Date(layout.created_at).toLocaleDateString();
    
    html += `
      <div class="saved-layout-card" onclick="loadLayout('${layout.id}')">
        <div class="sl-name">${layout.custom_name}</div>
        <div class="sl-meta">
          <span>🎯 ${plan.target_per_minute}/min</span>
          <span>⚡ ${plan.energy_plan.kw_per_output} kW/s</span>
        </div>
        <div class="sl-meta">
          <span>📅 ${date}</span>
          <button class="sl-del-btn" onclick="event.stopPropagation(); deleteLayout('${layout.id}')">🗑️</button>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
}

async function saveCurrentLayout() {
  if (!state.lastResult || !state.lastResult.plans.length) return;
  
  const bestPlan = state.lastResult.plans[0];
  const customName = prompt('Enter a name for this layout:', `${state.lastResult.item} - ${bestPlan.target_per_minute}/min`);
  
  if (!customName) return; // user cancelled

  try {
    const res = await fetch('/api/layouts/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        custom_name: customName,
        plan_data: bestPlan
      })
    });
    
    if (res.ok) {
      showToast('Layout saved!');
      loadSavedLayouts();
    }
  } catch (e) {
    alert('Failed to save layout.');
  }
}

async function deleteLayout(id) {
  if (!confirm('Delete this saved layout?')) return;
  try {
    await fetch(`/api/layouts/${id}`, { method: 'DELETE' });
    loadSavedLayouts();
  } catch (e) {
    console.error('Failed to delete', e);
  }
}

function loadLayout(id) {
  const layout = state.savedLayouts.find(l => l.id === id);
  if (!layout) return;
  
  const plan = layout.plan_data;
  
  // We can inject this saved plan back into the results view
  setResultsState('results');
  state.activeResultTab = 'best';
  updateResultTabButtons();

  // Fake a result object
  const resultData = {
    item: plan.chain.item,
    plans: [plan]
  };
  
  state.lastResult = resultData;
  renderSummaryCards(plan, resultData);
  renderChainTree(plan.chain);
  
  document.getElementById('compare-table').innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-dim)">Comparison not available for loaded saved layouts. Run a fresh optimization to compare.</div>';
  
  renderEnergyView(plan.energy_plan);
  renderRawInputs(plan.raw_inputs);
  
  showResultTab('best');
}

// ── Boot ───────────────────────────────────────────────────────────────────
init();
loadSavedLayouts();
