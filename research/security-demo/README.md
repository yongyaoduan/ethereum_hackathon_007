# Security pattern reference

Hash Scan's synthetic security cases use the reentrancy, faulty access-control and price-manipulation pattern families described in **Towards Automated Security Analysis of Smart Contracts based on Execution Property Graph**, arXiv:2305.14046v1 (Clue).

- [Original paper](https://arxiv.org/html/2305.14046v1), sections 5.3–5.5
- [Authors' project](https://rdi.berkeley.edu/clue/)

The examples illustrate the relationship between calls, storage updates, permission checks and asset flows. They do not reproduce Clue's execution-property-graph analysis. The hand-authored inputs are compact scenarios, not complete opcode traces or validated dependency graphs.

Three preserved HSK transactions provide withdrawal, funding and swap operation templates. Synthetic behavior is kept separate from these source snapshots and is not attributed to their real accounts. No attack-detection result is inferred from the source transactions.

The transaction-action vocabulary and the security-pattern vocabulary serve different purposes: action tags identify operations; an attack assessment additionally needs evidence about ordering, authorization and economic effects. The current product demonstrates that investigation flow without claiming deployed attack detection.

See [`demo/attack-lab/DATA-CONTRACT.md`](../../demo/attack-lab/DATA-CONTRACT.md) for the scenario schema, inputs and accounting boundaries.
