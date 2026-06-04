/*
  Power diagnostics UI adapter.

  Loaded after ui_diagnostics_adapter.js. It keeps the existing production and
  transport diagnostics, then appends a power/coal/steam recommendation block.
*/

function renderBottleneckDiagnostics(best, normalized) {
  const chainTree = document.getElementById('chain-tree');
  if (!chainTree || !best?.chain) return;

  renderProductionDiagnostics(chainTree, best, normalized);
  renderTransportDiagnostics(chainTree, normalized);
  renderPowerDiagnostics(chainTree, normalized);
}

function renderPowerDiagnostics(chainTree, normalized) {
  const power = normalized.diagnostics?.power || null;
  const summary = normalized.diagnostics?.power_summary || normalized.summary?.power_summary || {};

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!power) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">✅</span>
        <div class="cn-info">
          <div class="cn-name">Power Diagnostics</div>
          <div class="cn-machine">No power diagnostic data returned by backend.</div>
        </div>
        <div class="cn-stats">
          <span class="cn-count">unknown</span>
          <span class="cn-rate">power</span>
        </div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const level = power.level || summary.status || 'ok';
  const icon = level === 'critical' ? '🚨' : level === 'warning' ? '⚠️' : '⚡';
  const demandKw = Number(power.total_demand_kw || 0);
  const demandMw = Number(power.total_demand_mw || demandKw / 1000);
  const engines = Number(power.steam_engines || 0);
  const boilers = Number(power.boilers || 0);
  const coalPerSecond = Number(power.coal_per_second || 0);
  const coalPerMinute = Number(power.coal_per_minute || 0);
  const miners = Number(power.burner_coal_miners_required || 0);
  const headroom = Number(power.headroom_pct || 0);

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">${icon}</span>
      <div class="cn-info">
        <div class="cn-name">Power Diagnostics</div>
        <div class="cn-machine">
          ${demandKw.toFixed(1)} kW (${demandMw.toFixed(3)} MW) · ${engines} steam engine(s) · ${boilers} boiler(s)
        </div>
      </div>
      <div class="cn-stats">
        <span class="cn-count">${level}</span>
        <span class="cn-rate">power</span>
      </div>
    </div>
    <div class="cn-energy">
      ⚡ Capacity headroom: ${headroom.toFixed(1)}%
      &nbsp;·&nbsp; Coal: ${coalPerSecond.toFixed(3)}/s (${coalPerMinute.toFixed(1)}/min)
      &nbsp;·&nbsp; Burner coal miners: ×${miners}
      <br><span style="opacity:0.85">➡️ ${escapeHtml(power.recommendation || 'Build enough power production for the current plan.')}</span>
    </div>`;

  chainTree.appendChild(diagnostics);
}
