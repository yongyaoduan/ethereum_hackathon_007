# Label evaluation

## Current results

The Evaluation page uses the published [1,000-transaction collection](data/hackathon-scale), Jev predictions and the Astra judgments stored in each record’s `llm_judgment`. Results are recomputed from these records, not copied from an earlier run.

| Measure | Result | Scope |
| --- | ---: | --- |
| Valid model outputs | 999 / 1,000 | One input exceeded the model limit |
| Macro balanced accuracy | 91.3% | 32 labels with assessed positive and negative references |
| Exact label-set agreement | 82.2% | 870 fully assessed, valid outputs |
| Unvalidated labels | 13 / 45 | Not included in the macro score |

These are agreement results against Astra LLM references. No human review was performed. Full precision, confusion matrices and per-label counts are in [metrics.json](data/hackathon-scale/metrics.json). The manifest records the source file’s SHA-256.

## Sampling and provenance

The expanded pool contains 200 records from the original random cohort, 67 from action coverage, 140 development/regression records and 593 additional historical records. It includes 407 reused valid predictions and 592 new valid predictions.

The original random sampling selected blocks using a fixed seed, retrieved their transactions with full pagination, deduplicated hashes and froze the transaction list. This is a block-cluster sample, not a uniform sample of all HSK transactions. Action-coverage and additional records came from preserved chain evidence, protocol discovery and method/event searches. Each record retains `cohort` and `selection_origin`.

The expanded pool deliberately includes development records and reused predictions. Its aggregate is not a fresh independent held-out test. Protocol and block clustering also limit generalization to broader chain traffic. The transaction exploration pages continue to show the selected coverage collection; their filters do not alter Evaluation.

## Labels and references

The vocabulary contains 45 unique action names captured from Etherscan’s **By Actions** presets. The project defines an independent question for each action in [questions-v7.json](data/questions-v7.json). Jev evaluates all 45 in one request, using `typesafe/jev-1.13` and a 0.75 threshold. Multiple labels and empty label sets are valid outputs; execution status is separate metadata.

Current reference decisions use `llm_judgment.expected`, `llm_judgment.unassessed` and the evidence-based explanation in `llm_judgment.basis`. The older `reference` field is retained for provenance but does not determine current scores. These are neither official Etherscan annotations nor a human-reviewed gold standard.

Unassessed decisions are excluded per label, never converted to negatives. One failed model output has null predictions and is excluded from label scores rather than counted as a successful empty-label response. It remains in the original 1,000-record collection and in the export’s failure list.

## Metrics

For a label with assessed positive and negative examples:

```text
Sensitivity = TP / (TP + FN)
Specificity = TN / (TN + FP)
Balanced accuracy = (Sensitivity + Specificity) / 2
Macro balanced accuracy = mean balanced accuracy across evaluable labels
```

Exact-set agreement requires every predicted label to match on a fully assessed transaction. Of the 999 valid outputs, 870 have all reference decisions assessed; 715 of these match exactly. The other 129 valid outputs have at least one unassessed reference decision. A high macro score over 32 classes does not validate the remaining 13. Sparse classes and shared protocols also make population accuracy uncertain.

## Reproduce

```sh
python3 export_evaluation.py
```

This verifies the source manifest and recomputes [metrics.json](data/hackathon-scale/metrics.json), `site/dist/evaluation.json` and `site/dist/evaluation-evidence.json`. `evaluate.py` implements the metrics. `export_site.py` also invokes this exporter after rebuilding the separate transaction-view snapshot. Neither command calls a model or collects new chain data.

Evaluation loads its current scores and case index separately from the transaction views. Full chain evidence is loaded when a related transaction is opened. The downloadable results contain the source hash, cohort counts, per-class confusion matrices, reference judgments and failed-output IDs.

Security scenarios are assessed separately. Their labels are authored with synthetic cases; these action-label results do not establish attack-detection performance.
