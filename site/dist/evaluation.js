let evaluationData = null, evaluationRequest = null, evaluationEvidenceRequest = null;

function loadEvaluation() {
  if (!evaluationRequest) evaluationRequest = fetch('evaluation.json?v=1').then(r => {
    if (!r.ok) throw Error('Evaluation unavailable');
    return r.json();
  }).then(result => {
    if (result.schema_version !== 1 || result.metrics.n !== result.transactions.length) throw Error('Invalid evaluation');
    evaluationData = result;
    return result;
  }).catch(error => { evaluationRequest = null; throw error; });
  return evaluationRequest;
}

async function evaluationTransaction(id) {
  const result = await loadEvaluation();
  const transaction = result.transactions.find(t => t.id === id);
  if (!transaction || transaction.state) return transaction;
  if (!evaluationEvidenceRequest) evaluationEvidenceRequest = fetch('evaluation-evidence.json?v=1').then(r => {
    if (!r.ok) throw Error('Evidence unavailable');
    return r.json();
  }).catch(error => { evaluationEvidenceRequest = null; throw error; });
  const evidence = await evaluationEvidenceRequest;
  if (!evidence[id]) throw Error('Transaction evidence unavailable');
  transaction.state = evidence[id];
  return transaction;
}

async function renderEvaluation() {
  if (!evaluationData) {
    $('#evaluation-summary').innerHTML = '<div class="empty" role="status">Loading evaluation…</div>';
    $('#evaluation-rows').innerHTML = '';
    $('#evaluation-detail').innerHTML = '';
  }
  try { await loadEvaluation(); }
  catch (error) {
    $('#evaluation-summary').innerHTML = '<div class="empty" role="alert">Unable to load evaluation. <button id="retry-evaluation">Try again</button></div>';
    $('#retry-evaluation').onclick = renderEvaluation;
    return;
  }
  if (view !== 'evaluation') return;
  const {metrics: m, source: s, failures} = evaluationData;
  $('#evaluation-summary').innerHTML = `<div class="evaluation-context"><span>Jev · Astra reference agreement</span><a href="evaluation.json" download="hashscan-evaluation.json">Download results ↓</a></div><div class="evaluation-metrics"><div><span>Macro balanced accuracy · ${m.evaluated_labels} classes</span><strong>${pct(m.macro_balanced_accuracy)}</strong></div><div><span>Valid outputs</span><strong>${m.n.toLocaleString()}<small> / ${s.transaction_count.toLocaleString()}</small></strong></div><div><span>Exact-set agreement · ${m.exact_set_evaluated_transactions} assessed</span><strong>${pct(m.exact_set_accuracy)}</strong></div><div><span>Unvalidated labels</span><strong>${m.unvalidated_labels.length}</strong></div></div>`;
  $('#evaluation-rows').innerHTML = labels().map(l => {
    const r = m.per_label[l.id];
    return `<tr data-label="${l.id}" tabindex="0" aria-label="View ${esc(l.label)} performance"><td>${esc(l.label)}</td><td>${r.positives ? `${r.tp} / ${r.positives}<span class="recognition"><i class="correct" style="width:${r.tp/r.positives*100}%"></i><i class="miss" style="width:${r.fn/r.positives*100}%"></i></span>` : '<span class="unvalidated">No positive examples</span>'}</td><td class="${r.fp ? 'warning' : ''}">${r.fp} / ${r.negatives}</td><td class="${r.balanced_accuracy !== null && r.balanced_accuracy < .9 ? 'warning' : ''}">${r.balanced_accuracy == null ? '<span class="unvalidated">UNVALIDATED</span>' : pct(r.balanced_accuracy)}</td></tr>`;
  }).join('');
  document.querySelectorAll('[data-label]').forEach(e => bindSvg(e, () => {
    evaluationLabel = e.dataset.label;
    renderEvaluationDetail();
    if (innerWidth < 760) $('#evaluation-detail').scrollIntoView({behavior:'smooth', block:'start'});
  }));
  renderEvaluationDetail();
  $('#methodology').innerHTML = `<dl class="evaluation-method"><dt>Collection</dt><dd>${s.transaction_count.toLocaleString()} unique real HSK transactions. ${s.cohort_counts.original_fresh_random} original random, ${s.cohort_counts.original_fresh_coverage} action-coverage, ${s.cohort_counts.original_retired_regression} development/regression and ${s.cohort_counts.demo_unassessed} additional records. ${s.reused_outputs} outputs were reused and ${s.new_outputs} were newly classified. This expanded pool includes development records and is not an independent random test.</dd><dt>References</dt><dd>Astra judgments based on transaction evidence. No human review. Unassessed labels are excluded individually; they are not treated as negatives.</dd><dt>Scoring</dt><dd>Balanced accuracy averages positive and negative recall. The macro score averages ${m.evaluated_labels} labels with both positive and negative references. Exact-set agreement uses ${m.exact_set_evaluated_transactions} fully assessed valid outputs. Shared protocols and blocks limit generalization.</dd><dt>Classifier</dt><dd>${esc(s.classifier.model_requested)} · ${s.classifier.label_count} questions per request · threshold ${s.classifier.threshold} · questions v7.</dd><dt>Unavailable outputs</dt><dd>${failures.length} input exceeded the model limit and is excluded from label scores: ${failures.map(f => `<a href="https://hsk.blockscout.com/tx/${f.id}" target="_blank" rel="noopener">${short(f.id)} ↗</a>`).join(', ')}. It remains in the original collection with null predictions.</dd><dt>Source</dt><dd><a href="https://github.com/yongyaoduan/ethereum_hackathon_007/tree/main/data/hackathon-scale" target="_blank" rel="noopener">Transaction pool, manifest and computed metrics ↗</a><code class="evaluation-digest">SHA-256 ${esc(s.sha256)}</code></dd></dl>`;
  const requested = new URLSearchParams(location.hash.split('?')[1] || '').get('tx');
  if (requested && !$('#transaction-drawer').open) openEvidence(requested);
}

function renderEvaluationDetail() {
  if (!evaluationData) return;
  const l = label(evaluationLabel), r = evaluationData.metrics.per_label[l.id];
  const examples = evaluationData.transactions.filter(t => t.expected.includes(l.id) || t.predicted.includes(l.id));
  $('#evaluation-detail').innerHTML = `<div class="evaluation-label"><span class="action-tag" style="--tag:${actionColor(l.id)}">${esc(l.label)}</span></div><h2>${pct(r.balanced_accuracy)}</h2><div class="stat-pair"><span>Missed positives</span><b>${r.fn} / ${r.positives}</b></div><div class="stat-pair"><span>False positives</span><b>${r.fp} / ${r.negatives}</b></div><div class="stat-pair"><span>Unassessed</span><b>${r.unassessed}</b></div><details><summary>Statistical details</summary><div class="interval"><strong>Positive recall · 95% interval</strong>${wilson(r.tp,r.positives)}</div><div class="interval"><strong>Negative recall · 95% interval</strong>${wilson(r.tn,r.negatives)}</div><p>Wilson intervals assume independent observations. Shared protocols or blocks may reduce effective sample size.</p></details><details><summary>Action definition</summary><p>${esc(l.definition)}</p></details><h3 class="section-line">Related transactions <small>${examples.length}</small></h3><div class="evaluation-cases">${examples.map(t => {
    const status = t.unassessed.includes(l.id) ? 'Unassessed' : t.expected.includes(l.id) ? (t.predicted.includes(l.id) ? 'Matched' : 'Missed') : 'Extra label';
    return `<button class="example-link" data-evidence="${t.id}"><span>${short(t.id)}</span><small>${status}</small></button>`;
  }).join('') || '<span class="small">No positive or predicted examples</span>'}</div>`;
  document.querySelectorAll('#evaluation-rows tr').forEach(row => row.classList.toggle('selected-evaluation', row.dataset.label === evaluationLabel));
}
