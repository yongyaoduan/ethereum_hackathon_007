# Hash Scan

A Jev-powered transaction explorer for HashKey Chain. Hash Scan turns chain data into readable actions, connects those actions to asset movements, and lets users inspect the evidence behind a transaction.

The labeling pipeline is designed for fast, low-cost classification: one request evaluates the action vocabulary and returns structured decisions that the explorer can filter, compare and visualize.

[Open Hash Scan](https://hashscan.yy-duan.chatgpt.site) · [Run locally](#run-locally)

## Explore the app

| Page | What it shows | What you can do |
| --- | --- | --- |
| **Activity** | A moving activity field and transaction details | Choose up to six action lanes; filter the transaction table by date, action, status or address; inspect transfers and copy addresses. |
| **Explore** | The action vocabulary, frequency ranking and transaction distribution | Select an action to see matching transactions and related actions. |
| **Connections** | Actions that appear together, exact combinations and contract concentration | Compare relationships and open the transactions behind each connection. |
| **Evaluation** | Label-level agreement with Astra references across the expanded collection | Inspect class results, assessed examples and labels that remain unvalidated. |
| **Security** | A temporal view of reentrancy, access-control and price-manipulation scenarios | Open a case to inspect its mechanism, transfers, balance changes and original HSK source template. |

The transaction pages use captured HSK records and saved model predictions. Activity animates those historical records. Security uses explicitly marked synthetic scenarios, generated timestamps and example addresses; its linked HSK transactions provide operation templates, not evidence of actual attacks.

## Data sources

- **[HSK Blockscout](https://hsk.blockscout.com/):** transaction details, execution status, decoded input, paginated event logs, token transfers, internal calls and verified contract metadata. Original evidence is retained in [`data/evidence`](data/evidence) and [`data/contracts`](data/contracts).
- **[Etherscan Advanced Filter](https://etherscan.io/advanced-filter):** the *Presets → By Actions* vocabulary supplies the action names. Duplicate display names are consolidated into 45 labels. The capture and normalized vocabulary are in [`data/etherscan-presets-browser-capture.json`](data/etherscan-presets-browser-capture.json) and [`data/taxonomy.json`](data/taxonomy.json).
- **Security scenarios:** preserved HSK withdrawal, treasury-funding and swap transactions provide the starting operation types. Synthetic variants illustrate execution patterns described in [Clue](https://arxiv.org/html/2305.14046v1). Their data contract and source boundaries are documented in [`demo/attack-lab`](demo/attack-lab).

## Sampling

The original study used two complementary sampling methods:

- **Random sample:** select blocks within a fixed historical range using a recorded seed, retrieve every transaction in each selected block with full pagination, deduplicate by hash, then freeze the selected transaction IDs. System transactions, failures and transactions without matching actions are retained. This is a block-cluster sample, not a uniform sample of all HSK activity.
- **Action coverage sample:** find candidates through protocol histories, methods and events, then inspect complete transaction evidence. This broadens action coverage; its label frequencies do not represent network-wide activity.

The current [expanded collection](data/hackathon-scale) contains 1,000 unique real HSK transactions: 200 from the original random cohort, 67 from action coverage, 140 development/regression records and 593 additional historical records. Each record retains its source cohort and selection origin. The expanded assessment includes development records; it is not a fresh independent random test.

Against the saved Astra reference judgments, 999 valid Jev outputs achieve **91.3% macro balanced accuracy across 32 evaluable classes** and **82.2% exact label-set agreement on 870 fully assessed transactions**. One input exceeded the model limit and remains recorded as a failure. References have not been reviewed by humans, and 13 labels lack the positive or negative references needed for scoring. See [`EVALUATION.md`](EVALUATION.md) for the method and reproducible results.

Activity, Explore and Connections retain the selected action-coverage collection. Evaluation uses the expanded 1,000-transaction collection independently; the chart selection does not change its metrics.

## How tags are produced

1. Collect the transaction, receipt, logs, transfers, internal calls and available contract semantics.
2. Encode the evidence into a compact state. Reference annotations and expected answers are excluded from the model input.
3. Send one [Jev Decisions request](https://openrouter.ai/docs/guides/community/jev) containing an independent question for each action in the vocabulary.
4. Convert the returned scores into labels using the configured threshold. A transaction may have multiple labels or none.
5. Keep the labels connected to the source transaction so users can inspect the underlying evidence.

The implementation uses `typesafe/jev-1.13`; the current questions are in [`data/questions-v7.json`](data/questions-v7.json), and inference is implemented in [`run.py`](run.py). The label meanings are this project's operational definitions, not Etherscan's private classification rules. The original reference policy is documented in [`REFERENCE_POLICY.md`](REFERENCE_POLICY.md). Current evaluation references come from each expanded record’s `llm_judgment`; they are distinct from Jev predictions.

## Run locally

The complete app is static HTML, CSS and JavaScript. It requires Python for the local server and no frontend build step.

```sh
python3 -m http.server 8767 --directory site/dist
```

Open [http://localhost:8767](http://localhost:8767). Local review does not require access to the hosted deployment or an API key.

To inspect the inference options:

```sh
python3 run.py --help
```

A new model run accepts `OPENROUTER_API_KEY` from the environment or asks for it through a hidden prompt. Credentials are not included in the browser app.

## Repository map

| Path | Purpose |
| --- | --- |
| [`site/dist`](site/dist) | Application, saved transaction data and model predictions |
| [`data`](data) | Chain evidence, taxonomy, questions, sampling manifests and reference annotations |
| [`runs`](runs) | Model outputs and manifests used by the current data export |
| [`demo/attack-lab`](demo/attack-lab) | Synthetic security scenarios and their generator |
| `collect.py`, `enrich.py`, `sample.py` | Data collection, evidence enrichment and sampling |
| `compact.py`, `run.py`, `evaluate.py` | Model-state encoding, Jev inference and label evaluation |
| `export_site.py`, `export_evaluation.py` | Rebuild the product snapshot and the expanded Astra-reference evaluation |

## Direction

Hash Scan starts with readable transaction actions. The next steps are continuous ingestion, self-hosted inference through community Open-Jev, and reusable playbooks that extend the vocabulary toward security analysis. Those are extensions of the current explorer; the included Security cases demonstrate the intended investigation experience.
