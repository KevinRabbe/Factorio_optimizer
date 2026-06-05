/*
  Build list UI adapter.

  Loaded after diagnostics adapters. It appends dependency edge explanation and
  a logistics-strategy-aware build/shopping list to the Best Plan tab.
*/

(function installBuildListRenderer() {
  const previousRenderBottleneckDiagnostics = window.renderBottleneckDiagnostics || renderBottleneckDiagnostics;

  window.renderBottleneckDiagnostics = function patchedRenderBottleneckDiagnostics(best, normalized) {
    previousRenderBottleneckDiagnostics(best, normalized);
    const chainTree = document.getElementById('chain-tree');
    if (!chainTree) return;
    renderDependencyEdges(chainTree, normalized);
    renderBuildList(chainTree, normalized);
  };
})();

function renderDependencyEdges(chainTree, normalized) {
  const edges = normalized.diagnostics?.dependency_edges || [];
  const shown = edges.slice(0, 14);

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!shown.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">🔗</span>
        <div class="cn-info">
          <div class="cn-name">Dependency Edges</div>
          <div class="cn-machine">No dependency edge data returned.</div>
        </div>
        <div class="cn-stats"><span class="cn-count">0</span><span class="cn-rate">edges</span></div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const rows = shown.map(edge => `
    <div class="cn-energy" style="padding-left:${Math.min(edge.depth || 0, 5) * 14}px">
      ${escapeHtml(edge.source_icon || '📦')} <strong>${escapeHtml(edge.source_display_name)}</strong>
      <span style="opacity:0.75">from ${escapeHtml(edgeBlockLabel(edge.source_block) || edge.source_machine || 'source')}</span>
      &nbsp;→&nbsp;
      ${escapeHtml(edge.target_icon || '⚙️')} <strong>${escapeHtml(edge.target_display_name)}</strong>
      <span style="opacity:0.75">into ${escapeHtml(edgeBlockLabel(edge.target_block) || edge.target_machine || 'target')}</span>
      &nbsp;·&nbsp; ${Number(edge.required_per_minute || 0).toFixed(2)}/min
    </div>
  `).join('');

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">🔗</span>
      <div class="cn-info">
        <div class="cn-name">Dependency Edges</div>
        <div class="cn-machine">Shows exactly which item feeds which crafting/smelting step.</div>
      </div>
      <div class="cn-stats"><span class="cn-count">${shown.length}</span><span class="cn-rate">edges</span></div>
    </div>
    ${rows}`;

  chainTree.appendChild(diagnostics);
}

function renderBuildList(chainTree, normalized) {
  const buildList = normalized.diagnostics?.build_list || normalized.summary?.build_list || {};
  const items = buildList.items || [];
  const strategy = buildList.logistics_strategy || normalized.diagnostics?.logistics_strategy || state.logisticsStrategy || 'central_smelting';

  const diagnostics = document.createElement('div');
  diagnostics.className = 'chain-node';
  diagnostics.style.marginBottom = '10px';

  if (!items.length) {
    diagnostics.innerHTML = `
      <div class="chain-node-header">
        <span class="cn-icon">🧾</span>
        <div class="cn-info">
          <div class="cn-name">Build List</div>
          <div class="cn-machine">No build list data returned.</div>
        </div>
        <div class="cn-stats"><span class="cn-count">0</span><span class="cn-rate">items</span></div>
      </div>`;
    chainTree.appendChild(diagnostics);
    return;
  }

  const grouped = groupBuildListItems(items);
  const totals = summarizeBuildListItems(items);
  const totalChips = Object.entries(totals.byCategory).map(([category, count]) => `
    <span class="build-total-chip">${escapeHtml(categoryLabel(category))}: <strong>×${Number(count || 0)}</strong></span>
  `).join('');
  const rows = Object.entries(grouped).map(([block, blockItems]) => `
    <details class="build-block" ${block === 'local_crafting_block' ? 'open' : ''}>
      <summary>
        <span>${escapeHtml(blockLabel(block))}</span>
        <span class="build-summary-meta">${blockItems.length} rows · ${sumBuildCount(blockItems)} parts</span>
      </summary>
      ${renderBlockCategories(blockItems)}
    </details>
  `).join('');

  diagnostics.innerHTML = `
    <div class="chain-node-header">
      <span class="cn-icon">🧾</span>
      <div class="cn-info">
        <div class="cn-name">Build List</div>
        <div class="cn-machine">${escapeHtml(strategyLabel(strategy))} · approximate physical parts needed.</div>
      </div>
      <div class="cn-stats"><span class="cn-count">${totals.totalParts}</span><span class="cn-rate">parts</span></div>
    </div>
    <div class="build-total-row">${totalChips}</div>
    ${rows}`;

  chainTree.appendChild(diagnostics);
}

function renderBlockCategories(items) {
  const byCategory = {};
  for (const item of items) {
    const category = item.category || 'other';
    if (!byCategory[category]) byCategory[category] = [];
    byCategory[category].push(item);
  }

  return Object.entries(byCategory).map(([category, categoryItems]) => `
    <details class="build-category">
      <summary>
        <span>${escapeHtml(categoryLabel(category))}</span>
        <span class="build-summary-meta">×${sumBuildCount(categoryItems)}</span>
      </summary>
      ${categoryItems.map(item => `
        <div class="build-line-item">
          <span class="build-count">×${Number(item.count || 0)}</span>
          <span>${escapeHtml(item.display_name || item.entity)}</span>
          <span class="build-note">${escapeHtml(item.note || '')}</span>
        </div>
      `).join('')}
    </details>
  `).join('');
}

function summarizeBuildListItems(items) {
  const byCategory = {};
  let totalParts = 0;
  for (const item of items) {
    const count = Number(item.count || 0);
    const category = item.category || 'other';
    totalParts += count;
    byCategory[category] = (byCategory[category] || 0) + count;
  }
  return { totalParts, byCategory };
}

function sumBuildCount(items) {
  return items.reduce((sum, item) => sum + Number(item.count || 0), 0);
}

function groupBuildListItems(items) {
  const grouped = {};
  for (const item of items) {
    const block = item.logistics_block || 'local_crafting_block';
    if (!grouped[block]) grouped[block] = [];
    grouped[block].push(item);
  }
  return grouped;
}

function blockLabel(block) {
  const labels = {
    central_smelting_block: '🔥 Central Smelting Block',
    local_crafting_block: '🏭 Local Crafting Block',
    outpost_smelting_block: '🚂 Outpost Smelting Block',
    local_production_block: '📍 Local Production Block',
    power_block: '⚡ Power Block',
  };
  return labels[block] || block;
}

function edgeBlockLabel(block) {
  if (!block) return '';
  return blockLabel(block);
}

function categoryLabel(category) {
  const labels = {
    machines: '🏭 Machines',
    transport: '🚚 Belts / Lanes',
    inserters: '🦾 Inserters',
    power: '⚡ Power',
    other: '📦 Other',
  };
  return labels[category] || category;
}

function strategyLabel(strategy) {
  const labels = {
    central_smelting: 'Central Smelting strategy',
    local_smelting: 'Local Smelting strategy',
    outpost_smelting: 'Outpost Smelting strategy',
  };
  return labels[strategy] || strategy;
}
