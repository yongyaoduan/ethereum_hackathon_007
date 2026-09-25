# Label evaluation

## Scope

The action vocabulary contains the unique display names captured from Etherscan's **By Actions** presets. Each transaction is evaluated against every action independently. Multiple labels and empty label sets are valid outputs. Execution status is metadata; a failed attempt is not a completed action.

## Sampling and separation

Random sampling starts with a seeded selection of blocks from a fixed historical range. Every transaction in each selected block is retrieved with complete pagination, then hashes are deduplicated and a transaction sample is frozen. This produces a block-cluster sample. Class-coverage sampling separately retrieves candidates from protocol histories, methods and events.

Frozen manifests record transaction IDs, seeds, file hashes and split membership. Records used for prompt development are excluded from held-out scores. Some protocol families and block clusters overlap between splits, so the assessment does not establish unseen-protocol generalization.

## Reference annotations

Reference decisions use receipts, asset movements, event logs, internal calls and available contract semantics under the [reference policy](REFERENCE_POLICY.md). Method names retrieve candidates but do not establish labels by themselves. These annotations are project references, not official Etherscan labels or a human-reviewed gold standard.

Unresolved decisions are marked `unassessed` per label and excluded from that label's score. They are never silently converted to negatives or removed from the original random sample. Labels without assessed positive examples remain unvalidated.

## Metrics

For a label with assessed positive and negative examples:

```text
Sensitivity = TP / (TP + FN)
Specificity = TN / (TN + FP)
Balanced accuracy = (Sensitivity + Specificity) / 2
Macro balanced accuracy = mean balanced accuracy across evaluable labels
```

Exact-set agreement measures whether every label matches on a fully assessed transaction. Per-label confusion matrices and sample counts accompany the aggregate metrics. The Evaluation page provides the current saved results and supporting examples.

A high aggregate score over evaluable labels does not validate the entire vocabulary. Small samples and shared protocol/block clusters also limit what can be inferred about wider network accuracy.

## Reproducibility

`evaluate.py` computes metrics from saved predictions and reference annotations. The retained run directories hold the raw model responses, timing, usage and manifests used by the current app export. The regression run is development evidence and is excluded from held-out aggregates.

`export_site.py` rebuilds `site/dist/data.json` from those records. The export includes provenance for the historical collection; it does not collect new chain data or call a model.

Security scenarios are evaluated separately. Their labels are authored with synthetic cases; no security-model accuracy or detection of a real HSK attack is established by them.
