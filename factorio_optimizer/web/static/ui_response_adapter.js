/*
  UI response adapter.

  The backend now returns both the legacy response shape and the normalized
  compiler report shape. This adapter lets the existing UI prefer the new
  report contract while keeping compatibility with older /api/optimize output.
*/

function normalizeOptimizationResponse(data) {
  const report = data.report || null;
  const plans = (report && Array.isArray(report.plans)) ? report.plans : (data.plans || []);
  const bestPlan = data.best_plan || (report ? report.best_plan : null) || plans[0] || null;
  const summary = data.summary || (report ? report.summary : {}) || {};
  const diagnostics = data.diagnostics || (report ? report.diagnostics : {}) || {};

  return {
    raw: data,
    report,
    plans,
    bestPlan,
    summary,
    diagnostics,
    targetRatePerSecond: report?.target_rate_per_second ?? data.rate_per_second ?? bestPlan?.target_per_second ?? 0,
    targetRatePerMinute: report?.target_rate_per_minute ?? ((data.rate_per_second ?? 0) * 60),
    targetRatePerHour: report?.target_rate_per_hour ?? ((data.rate_per_second ?? 0) * 3600),
    bottlenecks: diagnostics.bottlenecks || [],
    bottleneckSummary: diagnostics.bottleneck_summary || summary.bottleneck_summary || {},
  };
}

function renderResults(data) {
  const normalized = normalizeOptimizationResponse(data);
  const best = normalized.bestPlan;

  if (!best) {
    setResultsState('placeholder');
    alert('Optimization returned no usable plan.');
    return;
  }

  state.lastResult = data;
  state.lastNormalizedResult = normalized;

  setResultsState('results');
  state.activeResultTab = 'best';
  updateResultTabButtons();

  renderSummaryCards(best, normalized.raw);
  renderTargetDiagnostics(best, normalized);
  renderBottleneckDiagnostics(best, normalized);

  if (best.chain) {
    renderChainTree(best.chain);
  }

  renderCompareTable(normalized.plans);

  if (best.energy_plan) {
    renderEnergyView(best.energy_plan);
  }

  renderRawInputs(best.raw_inputs || normalized.summary.raw_inputs || {});

  showResultTab('best');
}

function renderSummaryCards(best, data) {
  const normalized = normalizeOptimizationResponse(data);
  const exactMachines = getExactMachineCount(best);
  const roundedMachines = best.total_machines ?? 0;
  const targetPerMinute = normalized.targetRatePerMinute || best.target_per_minute || 0;
  const targetLabel = formatTargetRate(targetPerMinute);

  const html = `
    <div class="summary-card card-green">
      <div class="sc-icon">🎯</div>
      <div class="sc-value">${targetLabel}</div>
      <div class="sc-label">Target Output</div>
    </div>
    <div class="summary-card card-amber">
      <div class="sc-icon">🏭</div>
      <div class="sc-value">${exactMachines.toFixed(2)} → ${roundedMachines}</div>
      <div class="sc-label">Exact → Built Machines</div>
    </div>
    <div class="summary-card card-blue">
      <div class="sc-icon">⚡</div>
      <div class="sc-value">${formatKw(best.total_energy_kw || 0)}</div>
      <div class="sc-label">Power Draw</div>
    </div>
    <div class="summary-card card-purple">
      <div class="sc-icon">⏱️</div>
      <div class="sc-value">${best.avg_uptime_pct}%</div>
      <div class="sc-label">Avg Uptime</div>
    </div>`;
  document.getElementById('summary-cards').innerHTML = html;
}

function renderTargetDiagnostics(best, normalized) {
  const chainTree = document.getElementById('chain-tree');
  if (!chainTree) return;

  const targetPerSecond = normalized.targetRatePerSecond || best.target_per_second || 0;
  const targetPerMinute = normalized.targetRatePerMinute || best.target_per_minute || 0;
  const targetPerHour = normalized.targetRatePerHour || targetPerSecond * 3600;
  const exactMachines = getExactMachineCount(best);
  const roundedMachines = best.total_machines ?? 0;

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';
  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">🧪</span>
      <div class="cn-info">
        <div class="cn-name">Backend Target Diagnostics</div>
        <div class="cn-machine">
          ${targetPerSecond.toFixed(4)}/s · ${targetPerMinute.toFixed(2)}/min · ${targetPerHour.toFixed(1)}/hour
        </div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">exact ${exactMachines.toFixed(2)}</span>
        <span class="cn-rate">built ×${roundedMachines}</span>
      </div>
    </div>`;

  chainTree.innerHTML = '';
  chainTree.appendChild(diagnostics);
}

function renderBottleneckDiagnostics(best, normalized) {
  const chainTree = document.getElementById('chain-tree');
  if (!chainTree || !best?.chain) return;

  const candidates = normalized.bottlenecks && normalized.bottlenecks.length
    ? normalized.bottlenecks.map(fromBackendBottleneck)
    : collectBottleneckCandidates(best.chain);
  const summary = normalized.bottleneckSummary || {};
  const criticalCount = summary.critical_count ?? candidates.filter(candidate => candidate.level === 'critical').length;
  const warningCount = summary.warning_count ?? candidates.filter(candidate => candidate.level === 'warning').length;
  const shown = candidates.slice(0, 6);

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!shown.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">✅</span>
        <div class="cn-info">
          <div class="cn-name">Bottleneck Check</div>
          <div class="cn-machine">No obvious uptime bottlenecks or ratio inefficiencies found.</div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">stable</span>
          <span class="cn-rate">ok</span>
        </div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const rows = shown.map(candidate => `
    <div class="cn-energy">
      ${candidate.badge} ${candidate.icon} <strong>${candidate.displayName}</strong>
      &nbsp;·&nbsp; ${candidate.reason}
      &nbsp;·&nbsp; exact ${candidate.exact.toFixed(2)} → built ×${candidate.built}
      &nbsp;·&nbsp; uptime ${candidate.uptime.toFixed(1)}%
    </div>
  `).join('');

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">${criticalCount ? '🚧' : '⚠️'}</span>
      <div class="cn-info">
        <div class="cn-name">Bottleneck / Ratio Check</div>
        <div class="cn-machine">
          ${criticalCount} critical · ${warningCount} warning · backend report preferred, UI fallback available.
        </div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">${shown.length} shown</span>
        <span class="cn-rate">check</span>
      </div>
    </div>
    ${rows}`;

  chainTree.appendChild(diagnostics);
}

function renderChainTree(node, depth = 0) {
  const container = document.getElementById('chain-tree');
  if (depth === 0 && !container.querySelector('.chain-node')) {
    container.innerHTML = '';
  }

  const nodeEl = buildChainNodeEl(node, depth);
  if (depth === 0) {
    container.appendChild(nodeEl);
  }
  return nodeEl;
}

function fromBackendBottleneck(item) {
  const level = item.level || 'warning';
  return {
    item: item.item,
    displayName: item.display_name || item.item,
    icon: item.icon || '⚙️',
    exact: Number(item.exact_machines || 0),
    built: Number(item.built_machines || 0),
    uptime: Number(item.uptime_pct || 0),
    roundingWaste: Number(item.rounding_waste_pct || 0) / 100,
    level,
    badge: level === 'critical' ? '🚨' : '⚠️',
    reason: item.reason || 'backend bottleneck diagnostic',
    severity: Number(item.severity || 0),
  };
}

function collectBottleneckCandidates(root) {
  const candidates = [];

  function walk(node) {
    if (!node || node.is_raw) return;

    const uptime = Number(node.uptime_pct || 0);
    const exact = Number(node.machine_count_exact || 0);
    const built = Number(node.machine_count_ceil || 0);
    const roundingWaste = built > 0 ? Math.max(0, built - exact) / built : 0;
    const isCriticalUptime = uptime > 0 && uptime < 70;
    const isWarningUptime = uptime >= 70 && uptime < 90;
    const isWastefulRounding = roundingWaste > 0.30;

    if (isCriticalUptime || isWarningUptime || isWastefulRounding) {
      const level = isCriticalUptime ? 'critical' : 'warning';
      const reason = isCriticalUptime
        ? 'critical low machine uptime'
        : isWarningUptime
          ? 'ratio inefficiency warning'
          : 'rounding waste from ceil(machine count)';

      candidates.push({
        item: node.item,
        displayName: node.display_name || node.item,
        icon: node.icon || '⚙️',
        exact,
        built,
        uptime,
        roundingWaste,
        level,
        badge: level === 'critical' ? '🚨' : '⚠️',
        reason,
        severity: (100 - uptime) + (roundingWaste * 50) + (level === 'critical' ? 100 : 0),
      });
    }

    for (const child of (node.children || [])) walk(child);
  }

  walk(root);
  return candidates.sort((a, b) => b.severity - a.severity);
}

function getExactMachineCount(plan) {
  if (!plan || !plan.chain) return 0;
  return sumExactMachineCount(plan.chain);
}

function sumExactMachineCount(node) {
  if (!node || node.is_raw) return 0;
  const own = Number(node.machine_count_exact || 0);
  const children = Array.isArray(node.children) ? node.children : [];
  return own + children.reduce((total, child) => total + sumExactMachineCount(child), 0);
}

function formatTargetRate(perMinute) {
  if (perMinute >= 1000) return `${(perMinute / 1000).toFixed(1)}k/min`;
  if (perMinute >= 10) return `${perMinute.toFixed(0)}/min`;
  return `${perMinute.toFixed(2)}/min`;
}

function injectBlueprintButton() {
  const optimizeBtn = document.getElementById('optimize-btn');
  if (!optimizeBtn || document.getElementById('generate-blueprint-btn')) return;

  const btn = document.createElement('button');
  btn.className = 'optimize-btn';
  btn.id = 'generate-blueprint-btn';
  btn.disabled = !state.selectedItem;
  btn.style.marginTop = '10px';
  btn.style.background = 'linear-gradient(135deg, var(--blue), var(--purple))';
  btn.onclick = runGenerateModuleBlueprint;
  btn.innerHTML = '<span class="optimize-icon">📐</span><span id="generate-blueprint-btn-text">Generate Blueprint</span>';

  optimizeBtn.insertAdjacentElement('afterend', btn);
}

function updateBlueprintButtonState() {
  const btn = document.getElementById('generate-blueprint-btn');
  const text = document.getElementById('generate-blueprint-btn-text');
  if (!btn || !text) return;

  btn.disabled = !state.selectedItem;
  text.textContent = state.selectedItem
    ? `Generate Blueprint — ${state.selectedItem.display_name}`
    : 'Generate Blueprint';
}

async function runGenerateModuleBlueprint() {
  if (!state.selectedItem) return;

  const btn = document.getElementById('generate-blueprint-btn');
  const text = document.getElementById('generate-blueprint-btn-text');
  const oldText = text ? text.textContent : '';

  if (btn) btn.disabled = true;
  if (text) text.textContent = 'Generating blueprint…';
  setResultsState('loading');

  try {
    const res = await fetch('/api/generate-module-blueprint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        recipe_name: state.selectedItem.name,
        era: state.machineEra,
        machine_name: selectedBlueprintMachineName(),
        seed: 0,
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Blueprint generation failed.');

    state.lastBlueprintReport = data;
    renderModuleBlueprintReport(data);
  } catch (err) {
    setResultsState('placeholder');
    alert(`Blueprint generation failed: ${err.message}`);
  } finally {
    if (btn) btn.disabled = !state.selectedItem;
    if (text) text.textContent = oldText || `Generate Blueprint — ${state.selectedItem?.display_name || ''}`;
  }
}

function selectedBlueprintMachineName() {
  const category = state.selectedItem?.category || '';
  const era = state.machineEra || 'early';

  if (category === 'raw') return null;
  if (category === 'intermediate' && isLikelySmeltingRecipe(state.selectedItem?.name)) {
    return selectedFurnaceMachineName();
  }

  if (era === 'early') return 'assembling_machine_1';
  if (era === 'mid') return 'assembling_machine_2';
  if (era === 'end') return 'assembling_machine_3';
  return 'assembling_machine_1';
}

function selectedFurnaceMachineName() {
  const era = state.machineEra || 'early';
  if (era === 'early') return 'stone_furnace';
  if (state.useElectricFurnace) return 'electric_furnace';
  return 'steel_furnace';
}

function isLikelySmeltingRecipe(itemName) {
  return [
    'iron_plate',
    'copper_plate',
    'steel_plate',
    'stone_brick',
  ].includes(itemName);
}

function renderModuleBlueprintReport(report) {
  setResultsState('results');
  state.activeResultTab = 'best';
  updateResultTabButtons();

  document.getElementById('summary-cards').innerHTML = `
    <div class="summary-card ${report.structure_valid ? 'card-green' : 'card-purple'}">
      <div class="sc-icon">🏗️</div>
      <div class="sc-value">${report.structure_valid ? 'PASS' : 'FAIL'}</div>
      <div class="sc-label">Structure</div>
    </div>
    <div class="summary-card ${report.recipe_valid ? 'card-green' : 'card-purple'}">
      <div class="sc-icon">🧪</div>
      <div class="sc-value">${report.recipe_valid ? 'PASS' : 'FAIL'}</div>
      <div class="sc-label">Recipe</div>
    </div>
    <div class="summary-card ${report.connection_valid ? 'card-green' : 'card-purple'}">
      <div class="sc-icon">🔌</div>
      <div class="sc-value">${report.connection_valid ? 'PASS' : 'FAIL'}</div>
      <div class="sc-label">Connections</div>
    </div>
    <div class="summary-card card-blue">
      <div class="sc-icon">📐</div>
      <div class="sc-value">${report.width}×${report.height}</div>
      <div class="sc-label">Module Size</div>
    </div>`;

  const errors = report.validation_errors && report.validation_errors.length
    ? report.validation_errors.map(error => `<div class="cn-energy">❌ ${escapeHtml(error)}</div>`).join('')
    : '<div class="cn-energy">✅ No validation errors.</div>';

  document.getElementById('chain-tree').innerHTML = `
    <div class="chain-node">
      <div class="chain-node-header">
        <span class="cn-icon">📐</span>
        <div class="cn-info">
          <div class="cn-name">Generated Module Blueprint: ${escapeHtml(report.recipe_name)}</div>
          <div class="cn-machine">${escapeHtml(report.module_type)} · ${escapeHtml(report.machine_name || 'auto machine')}</div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">${report.valid ? 'valid' : 'invalid'}</span>
          <span class="cn-rate">blueprint</span>
        </div>
      </div>
      ${errors}
    </div>
    <div class="chain-node">
      <div class="chain-node-header">
        <span class="cn-icon">🧱</span>
        <div class="cn-info">
          <div class="cn-name">ASCII Layout</div>
          <div class="cn-machine">Generated from FactoryModule → BlueprintPlan</div>
        </div>
      </div>
      <pre style="white-space:pre; overflow:auto; padding:12px; color:var(--text); background:rgba(0,0,0,0.22); border-radius:10px;">${escapeHtml(report.ascii || '')}</pre>
    </div>
    <div class="chain-node">
      <div class="chain-node-header">
        <span class="cn-icon">📋</span>
        <div class="cn-info">
          <div class="cn-name">Blueprint String</div>
          <div class="cn-machine">Copy and import in Factorio.</div>
        </div>
        <div class="cn-stats">
          <button class="save-layout-btn" onclick="copyGeneratedBlueprintString()">Copy</button>
        </div>
      </div>
      <pre id="generated-blueprint-string" style="white-space:pre-wrap; word-break:break-all; overflow:auto; max-height:160px; padding:12px; color:var(--text); background:rgba(0,0,0,0.22); border-radius:10px;">${escapeHtml(report.blueprint_string || '')}</pre>
    </div>`;

  document.getElementById('compare-table').innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-dim)">Blueprint generation does not compare production plans yet.</div>';
  document.getElementById('energy-view').innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-dim)">Energy view is available for full optimization plans.</div>';
  document.getElementById('raw-inputs-view').innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-dim)">Raw input view is available for full optimization plans.</div>';

  showResultTab('best');
}

async function copyGeneratedBlueprintString() {
  const value = state.lastBlueprintReport?.blueprint_string || '';
  if (!value) return;

  try {
    await navigator.clipboard.writeText(value);
    showToast();
  } catch (_err) {
    prompt('Copy blueprint string:', value);
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

(function installBlueprintUiAdapter() {
  injectBlueprintButton();
  updateBlueprintButtonState();

  const originalSelectItem = window.selectItem;
  if (typeof originalSelectItem === 'function') {
    window.selectItem = function patchedSelectItem(item) {
      originalSelectItem(item);
      updateBlueprintButtonState();
    };
  }
})();

(function loadProductionDiagnosticsAdapter() {
  if (document.querySelector('script[src="/ui_diagnostics_adapter.js"]')) return;
  const script = document.createElement('script');
  script.src = '/ui_diagnostics_adapter.js';
  document.body.appendChild(script);
})();
