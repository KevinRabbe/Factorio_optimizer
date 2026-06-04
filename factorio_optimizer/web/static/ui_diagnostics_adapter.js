/*
  Diagnostics UI adapter.

  Backend diagnostics now classify final-process requirements separately from
  upstream scaling requirements. This renderer makes that visible in the UI:
  upstream gears/cables/plates are shown as "scale production", not as hard
  bottlenecks. It also renders transport/inserter capacity diagnostics.
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
          <div class="cn-machine">No belt or inserter saturation warnings found at the current target rate.</div>
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
      &nbsp;·&nbsp; ${Number(item.utilization_pct || 0).toFixed(1)}% of ${escapeHtml(item.selected_entity || 'entity')}
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
          ${criticalCount} critical · ${warningCount} warning · checks belt and inserter item/s limits.
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
