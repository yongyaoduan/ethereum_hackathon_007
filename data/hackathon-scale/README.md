# Hash Scan · 1,000 HSK transactions

[`transactions.json`](transactions.json) contains **1,000 unique real HashKey Chain transactions**, their saved Jev outputs, source cohorts and Astra reference judgments.

| Item | Count |
| --- | ---: |
| Unique transactions | 1,000 |
| Successful Jev classifications | 999 |
| Reused successful classifications | 407 |
| New successful classifications | 592 |
| Input-too-long records retained | 1 |
| Astra reference judgments | 1,000 |

The JSON is an array, one object per transaction. Its SHA-256 and exact counts are in [`manifest.json`](manifest.json).

## Fields

| Field | Meaning |
| --- | --- |
| `id` | Transaction hash |
| `state` | Chain evidence: transaction, logs, token transfers, internal calls and contract context |
| `classification_status` | `classified` or `input_too_long` |
| `predicted` | Jev action IDs; multiple labels or an empty list are valid results |
| `confidence` | Jev scores for the 45 action labels |
| `reused`, `source_run` | Whether the output was reused and its original run |
| `cohort`, `selection_origin` | Original study cohort and transaction-selection provenance |
| `reference` | Existing study reference labels, unassessed labels and supporting basis |
| `llm_judgment` | Astra reference: `expected`, `unassessed` and `basis` |
| `single_request_seconds` | Recorded model-request duration |
| `model`, `model_requested` | Returned and requested model identities |
| `state_sha256`, `evidence_sha256` | Source-state and evidence identifiers |

For the input-too-long record, `predicted` and `confidence` are `null`; its full transaction and failure status remain in the array. Do not convert that record into an empty-label success. `llm_judgment` is an LLM reference, not a human annotation.

The classifier uses `typesafe/jev-1.13`, the existing [v7 questions](../questions-v7.json), 45 action labels and a 0.75 threshold. This expanded pool retains the original random, coverage and development/regression cohorts; it is not a fresh independent random test.

## Load the data

```javascript
const transactions = await fetch('data/hackathon-scale/transactions.json')
  .then(response => response.json());
const classified = transactions.filter(tx => tx.classification_status === 'classified');
```

This is the complete data export for the expanded collection. The existing `site/dist/data.json` is a separate product export with its own schema and selected display cohort.
