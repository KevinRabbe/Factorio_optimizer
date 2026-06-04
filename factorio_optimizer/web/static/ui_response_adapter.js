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
  renderBottleneckDiagnostics(best);

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

function renderBottleneckDiagnostics(best) {
  const chainTree = document.getElementById('chain-tree');
  if (!chainTree || !best?.chain) return;

  const candidates = collectBottleneckCandidates(best.chain);
  const worst = candidates.slice(0, 5);

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!worst.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">✅</span>
        <div class="cn-info">
          <div class="cn-name">Bottleneck Check</div>
          <div class="cn-machine">No obvious uptime bottlenecks found in the current production chain.</div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">stable</span>
          <span class="cn-rate">ok</span>
        </div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const rows = worst.map(candidate => `
    <div class="cn-energy">
      ${candidate.icon} <strong>${candidate.displayName}</strong>
      &nbsp;·&nbsp; ${candidate.reason}
      &nbsp;·&nbsp; exact ${candidate.exact.toFixed(2)} → built ×${candidate.built}
      &nbsp;·&nbsp; uptime ${candidate.uptime.toFixed(1)}%
    </div>
  `).join('');

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">🚧</span>
      <div class="cn-info">
        <div class="cn-name">Bottleneck Candidates</div>
        <div class="cn-machine">Lowest machine uptime / highest rounding waste first.</div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">${worst.length} shown</span>
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

function collectBottleneckCandidates(root) {
  const candidates = [];

  function walk(node) {
    if (!node || node.is_raw) return;

    const uptime = Number(node.uptime_pct || 0);
    const exact = Number(node.machine_count_exact || 0);
    const built = Number(node.machine_count_ceil || 0);
    const roundingWaste = built > 0 ? Math.max(0, built - exact) / built : 0;
    const isLowUptime = uptime > 0 && uptime < 70;
    const isWastefulRounding = roundingWaste > 0.30;

    if (isLowUptime || isWastefulRounding) {
      candidates.push({
        item: node.item,
        displayName: node.display_name || node.item,
        icon: node.icon || '⚙️',
        exact,
        built,
        uptime,
        roundingWaste,
        reason: isLowUptime
          ? 'low machine uptime'
          : 'rounding waste from ceil(machine count)',
        severity: (100 - uptime) + (roundingWaste * 50),
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
