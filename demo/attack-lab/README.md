# Security scenarios

This directory contains synthetic examples for the Security page: reentrancy, faulty access control and price manipulation. Each pattern has a baseline and an attack variant. The examples preserve real HSK source transactions as operation templates and construct separate hypothetical calls, state changes and transfers.

The pattern definitions draw on [Clue, sections 5.3–5.5](https://arxiv.org/html/2305.14046v1). See the [data contract](DATA-CONTRACT.md) for the evidence boundaries and accounting rules.

## Files

| File | Purpose |
| --- | --- |
| `cases.json` | Source snapshots and synthetic cases |
| `build_data.py` | Deterministic scenario generator from captured transaction records |
| `index.template.html` | Standalone scenario viewer template |
| `build.py` | Builds the standalone viewer with embedded data |
| `index.html` | Prebuilt standalone viewer |

The integrated product page is in [`site/dist`](../../site/dist), with the same cases in `security-data.json`. It adds a generated event timeline, case navigation and display-only example addresses. Real source timestamps and explorer links remain separate from simulated events.

## Generate the standalone viewer

Python's standard library is sufficient:

```sh
python3 build_data.py /path/to/transactions.json cases.json
python3 build.py
```

Open `index.html` to inspect the standalone cases. The integrated application can be run from the repository root with the server command in the main README.

## Interpretation

Source transactions are not attack evidence. The cases are authored simulations, not EVM replays or model predictions. Asset transfers conserve the declared balances; collateral claims and outstanding debt are represented separately from cash. A cash surplus does not establish profit.

For a future detector integration, send only `variant.model_input`; keep scenario names, reference labels and display explanations outside the request. `model_result` remains null until an actual model response is recorded.
