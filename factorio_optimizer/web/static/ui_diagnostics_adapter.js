/*
  Diagnostics UI adapter.

  Backend diagnostics now classify final-process requirements separately from
  upstream scaling requirements. This renderer makes that visible in the UI:
  upstream gears/cables/plates are shown as "scale production", not as hard
  bottlenecks. It also renders transport/inserter capacity diagnostics and
  adds belt/inserter selector controls.
*/

function renderBottleneckDiagnostics(best, normalized) {
  const chainTree = document.getElementById('chain-tree');
  if (!chainTree || !best?.chain) return;

  renderProductionDiagnostics(chainTree, best, normalized);
  renderTransportDiagnostics(chainTree, normalized);
}

function renderProductionDiagnostics(chainTree, best, normalized) {
  const candidates = normalized.bottlenecks && normalized.bottlenecks.length
    ? normalized.bottlenecks.map(fromBackendBottleneck)
    : collectBottleneckCandidates(best.chain);
  const summary = normalized.bottleneckSummary || {};

  const trueBottlenecks = candidates.filter(candidate =>
    candidate.kind === 'final_production_requirement' && candidate.level !== 'info'
  );
  const scalingRequirements = candidates.filter(candidate =>
    candidate.kind === 'intermediate_scaling_requirement'
  );
  const ratioWarnings = candidates.filter(candidate =>
    candidate.kind === 'ratio_inefficiency'
  );

  const shown = [
    ...trueBottlenecks,
    ...scalingRequirements,
    ...ratioWarnings,
  ].slice(0, 8);

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!shown.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">✅</span>
        <div class="cn-info">
          <div class="cn-name">Production Diagnostics</div>
          <div class="cn-machine">No final bottlenecks or upstream scaling warnings found.</div>
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
      &nbsp;·&nbsp; target ${candidate.targetPerMinute.toFixed(2)}/min
      &nbsp;·&nbsp; exact ${candidate.exact.toFixed(2)} → build ×${candidate.built}
      &nbsp;·&nbsp; uptime ${candidate.uptime.toFixed(1)}%
      <br><span style="opacity:0.85">➡️ ${escapeHtml(candidate.recommendation)}</span>
    </div>
  `).join('');

  const trueCount = summary.true_bottleneck_count ?? trueBottlenecks.length;
  const scalingCount = summary.scaling_count ?? scalingRequirements.length;
  const warningCount = summary.warning_count ?? candidates.filter(candidate => candidate.level === 'warning').length;
  const icon = trueCount ? '🚧' : scalingCount ? '🏭' : '⚠️';

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">${icon}</span>
      <div class="cn-info">
        <div class="cn-name">Production Diagnostics</div>
        <div class="cn-machine">
          ${trueCount} true bottleneck · ${scalingCount} scalable upstream requirement · ${warningCount} warning.
        </div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">${shown.length} shown</span>
        <span class="cn-rate">math</span>
      </div>
    </div>
    ${rows}`;

  chainTree.appendChild(diagnostics);
}

function renderTransportDiagnostics(chainTree, normalized) {
  const transport = normalized.diagnostics?.transport || [];
  const summary = normalized.diagnostics?.transport_summary || normalized.summary?.transport_summary || {};
  const relevant = transport
    .filter(item => item.level === 'critical' || item.level === 'warning')
    .slice(0, 8);

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!relevant.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">✅</span>
        <div class="cn-info">
          <div class="cn-name">Transport / Inserter Diagnostics</div>
          <div class="cn-machine">
            ${transportSelectorSummary()} · no belt or inserter saturation warnings found.
          </div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">stable</span>
          <span class="cn-rate">flow</span>
        </div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const rows = relevant.map(item => `
    <div class="cn-energy">
      ${transportBadge(item)} ${escapeHtml(item.icon || '📦')} <strong>${escapeHtml(item.display_name || item.item)}</strong>
      &nbsp;·&nbsp; ${transportKindLabel(item.kind)}
      &nbsp;·&nbsp; ${Number(item.required_per_second || 0).toFixed(2)}/s
      &nbsp;·&nbsp; ${Number(item.utilization_pct || 0).toFixed(1)}% of ${escapeHtml(entityDisplayName(item.selected_entity || 'entity'))}
      <br><span style="opacity:0.85">➡️ ${escapeHtml(item.recommendation || '')}</span>
    </div>
  `).join('');

  const criticalCount = summary.critical_count ?? relevant.filter(item => item.level === 'critical').length;
  const warningCount = summary.warning_count ?? relevant.filter(item => item.level === 'warning').length;
  const icon = criticalCount ? '🚧' : '⚠️';

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">${icon}</span>
      <div class="cn-info">
        <div class="cn-name">Transport / Inserter Diagnostics</div>
        <div class="cn-machine">
          ${criticalCount} critical · ${warningCount} warning · ${transportSelectorSummary()}.
        </div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">${relevant.length} shown</span>
        <span class="cn-rate">flow</span>
      </div>
    </div>
    ${rows}`;

  chainTree.appendChild(diagnostics);
}

function fromBackendBottleneck(item) {
  const kind = item.kind || 'ratio_inefficiency';
  const level = item.level || 'warning';
  return {
    item: item.item,
    displayName: item.display_name || item.item,
    icon: item.icon || '⚙️',
    kind,
    exact: Number(item.exact_machines || 0),
    built: Number(item.built_machines || 0),
    uptime: Number(item.uptime_pct || 0),
    roundingWaste: Number(item.rounding_waste_pct || 0) / 100,
    targetPerSecond: Number(item.target_per_second || 0),
    targetPerMinute: Number(item.target_per_minute || 0),
    level,
    badge: badgeForDiagnostic(kind, level),
    reason: item.reason || reasonForDiagnostic(kind, level),
    recommendation: item.recommendation || recommendationForDiagnostic(kind),
    severity: Number(item.severity || 0),
  };
}

function badgeForDiagnostic(kind, level) {
  if (kind === 'intermediate_scaling_requirement') return '🏭';
  if (level === 'critical') return '🚨';
  if (level === 'warning') return '⚠️';
  return 'ℹ️';
}

function transportBadge(item) {
  if (item.level === 'critical') return '🚨';
  if (item.level === 'warning') return '⚠️';
  return '✅';
}

function transportKindLabel(kind) {
  if (kind === 'belt_capacity') return 'belt capacity';
  if (kind === 'inserter_capacity') return 'inserter capacity';
  return kind || 'transport capacity';
}

function reasonForDiagnostic(kind, level) {
  if (kind === 'intermediate_scaling_requirement') return 'scale upstream production';
  if (kind === 'final_production_requirement') return 'final crafting process requirement';
  if (level === 'critical') return 'critical bottleneck';
  return 'ratio inefficiency';
}

function recommendationForDiagnostic(kind) {
  if (kind === 'intermediate_scaling_requirement') return 'Build more upstream production for this item.';
  if (kind === 'final_production_requirement') return 'Build enough final machines and verify final input delivery.';
  return 'Accept idle time or scale the target rate to a cleaner ratio.';
}

function injectTransportTechSelectors() {
  if (document.getElementById('transport-tech-section')) return;

  state.beltName = state.beltName || defaultBeltForEra(state.machineEra);
  state.inserterName = state.inserterName || defaultInserterForEra(state.machineEra);

  const anchor = document.getElementById('furnace-section') || document.getElementById('module-section');
  if (!anchor) return;

  const section = document.createElement('div');
  section.className = 'config-section';
  section.id = 'transport-tech-section';
  section.innerHTML = `
    <label class="config-label">🚚 Transport Tech
      <span class="label-note">Used for belt / inserter diagnostics</span>
    </label>
    <div class="rate-row" style="margin-bottom:8px">
      <select id="belt-tech-select" class="rate-unit-select" style="width:100%" onchange="setBeltTech(this.value)">
        <option value="transport_belt">Yellow Belt · 15/s</option>
        <option value="fast_transport_belt">Red Belt · 30/s</option>
        <option value="express_transport_belt">Blue Belt · 45/s</option>
      </select>
    </div>
    <div class="rate-row">
      <select id="inserter-tech-select" class="rate-unit-select" style="width:100%" onchange="setInserterTech(this.value)">
        <option value="burner_inserter">Burner Inserter · ~0.60/s</option>
        <option value="inserter">Inserter · ~0.83/s</option>
        <option value="fast_inserter">Fast Inserter · ~2.31/s</option>
        <option value="stack_inserter">Stack Inserter · ~12/s</option>
      </select>
    </div>`;

  anchor.insertAdjacentElement('afterend', section);
  syncTransportTechSelectorsToState();
}

function setBeltTech(value) {
  state.beltName = value;
}

function setInserterTech(value) {
  state.inserterName = value;
}

function syncTransportTechSelectorsToState() {
  const belt = document.getElementById('belt-tech-select');
  const inserter = document.getElementById('inserter-tech-select');
  if (belt) belt.value = state.beltName || defaultBeltForEra(state.machineEra);
  if (inserter) inserter.value = state.inserterName || defaultInserterForEra(state.machineEra);
}

function maybeResetTransportTechForEra() {
  state.beltName = defaultBeltForEra(state.machineEra);
  state.inserterName = defaultInserterForEra(state.machineEra);
  syncTransportTechSelectorsToState();
}

function defaultBeltForEra(era) {
  if (era === 'end') return 'express_transport_belt';
  return 'transport_belt';
}

function defaultInserterForEra(era) {
  if (era === 'early') return 'inserter';
  if (era === 'mid') return 'fast_inserter';
  if (era === 'end') return 'stack_inserter';
  return 'inserter';
}

function transportSelectorSummary() {
  return `${entityDisplayName(state.beltName || defaultBeltForEra(state.machineEra))} · ${entityDisplayName(state.inserterName || defaultInserterForEra(state.machineEra))}`;
}

function entityDisplayName(name) {
  const names = {
    transport_belt: 'Yellow Belt',
    fast_transport_belt: 'Red Belt',
    express_transport_belt: 'Blue Belt',
    burner_inserter: 'Burner Inserter',
    inserter: 'Inserter',
    fast_inserter: 'Fast Inserter',
    stack_inserter: 'Stack Inserter',
  };
  return names[name] || String(name).replaceAll('_', ' ');
}

(function installTransportTechUiAdapter() {
  injectTransportTechSelectors();

  const originalRunOptimize = window.runOptimize;
  window.runOptimize = async function patchedRunOptimize() {
    if (!state.selectedItem) return;

    const rate = parseFloat(document.getElementById('rate-input').value) || 1;
    const unit = document.getElementById('rate-unit').value;

    const body = {
      item: state.selectedItem.name,
      rate,
      unit,
      era: state.machineEra,
      use_electric_furnace: state.useElectricFurnace,
      belt_name: state.beltName || defaultBeltForEra(state.machineEra),
      inserter_name: state.inserterName || defaultInserterForEra(state.machineEra),
      modules: getModuleConfigs(),
    };

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
  };

  const originalUpdateFurnaceSection = window.updateFurnaceSection;
  if (typeof originalUpdateFurnaceSection === 'function') {
    window.updateFurnaceSection = function patchedUpdateFurnaceSection() {
      originalUpdateFurnaceSection();
      maybeResetTransportTechForEra();
    };
  }

  // Keep a reference for debugging in DevTools if needed.
  window.originalRunOptimizeWithoutTransportSelectors = originalRunOptimize;
})();
