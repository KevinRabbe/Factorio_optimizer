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
