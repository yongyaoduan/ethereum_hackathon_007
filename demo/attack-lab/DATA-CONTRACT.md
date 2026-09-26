# Synthetic attack demonstration data contract

`cases.json` is version `1.0.0`: three groups, each with one `benign` and one `attack` variant. It illustrates reentrancy, faulty access control and price manipulation using synthetic accounting and ordered events. The scenario families adapt [Clue v1, sections 5.3–5.5](https://arxiv.org/html/2305.14046v1), as documented in [the reference note](../../research/security-demo/README.md). This is not a reproduction of Clue.

All six specimens are **synthetic counterfactuals** authored for this project. They are not actual HSK attacks, contract execution traces, EVM replays, human-reviewed annotations, or detector results. The real transaction supplies provenance and an operation template only. Injected behavior must never be attributed to its real addresses or contracts.

## Structure used by the frontend

```text
{
  schema_version, origin, title_zh, disclaimer_zh, annotation_policy, reference,
  groups: [{
    id, title_zh, attack_type,
    source_transaction: {
      hash, chain_id: 177, method, timestamp, block, explorer_url,
      state_sha256, upstream_state_sha256, original_state, usage
    },
    variants: [{
      id, variant: "benign" | "attack", origin, title_zh, summary,
      changed_fields: [string], model_result: null,
      reference_annotation: {author, basis, attack_labels: [string], rationale},
      model_input: {
        origin, hypothetical: true, transaction, actor_roles, assumptions,
        pre_state: {balances, storage},
        call_trace: [{order, hypothetical, id, parent_id, from, to, method, arguments, result}],
        storage_accesses: [{order, hypothetical, call_id, operation, key, value? , before?, after?}],
        control_checks: [{order, hypothetical, call_id, expression, observed_value, enforced, branch}],
        asset_transfers: [{order, hypothetical, call_id, from, to, asset, amount}],
        post_state: {balances, storage}
      },
      display: {
        steps: [{order, title, detail, kind}],
        balances_before_after: [{actor, asset, before, after, delta}],
        metrics: [{label, value, unit}]
      }
    }]
  }]
}
```

`origin` is always `synthetic_counterfactual`. Group IDs and attack labels are `reentrancy`, `faulty_access_control`, and `price_manipulation`. Benign references have `attack_labels: []`. Every annotation has `author: "assistant scenario author"`; the reference label is predefined by construction, not evidence of model correctness. The source category labels from the existing transaction classifier are not reused as security results.

Model input is **only** `variant.model_input`. Do not send IDs, group/category titles, variant names, reference labels/rationale, changed fields, display text, or source snapshot to a future attack detector. The model input has no expected label or `attack_detected` field. Neutral actor aliases are not real addresses. Its transaction has `hash: null`, `chain_id: null`; it must never become a purported HSK transaction. All events and balances are hypothetical.

`order` is globally increasing across the four event arrays; merge and sort by order to recover the authored sequence. `parent_id` links nested calls, and `call_id` links operations to a call. These are compact manually constructed traces, not opcode-complete traces or validated control/data dependence graphs. `display.steps` is a 4–6 step explanatory summary and has its own order. Kinds are `read`, `write`, `call`, `check`, `transfer`, or `state`.

All amounts use decimal strings in display units. Balances are `balances[actor][asset]`. Signed `delta` is after minus before. Post balances follow the authored asset transfers. Storage includes claims, collateral and debt positions; these are not extra physical token balances. Gas costs are omitted.

## Source snapshot preservation

`source_transaction.original_state` is copied without modification from the actual selected transaction's `state` in the merged source data. `state_sha256` hashes its canonical UTF-8 JSON with sorted keys, no whitespace separators and literal Unicode (Python `json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). The upstream digest is separately preserved as `upstream_state_sha256`; it may describe a compacted state rather than this complete snapshot. The source hash/explorer link is labeled as an operation template, not attack evidence. No synthetic call or amount changes the preserved source.

| Group | Actual source method | Synthetic adaptation |
| --- | --- | --- |
| Reentrancy | `withdraw` | Toy vault 100 HSK, one actor credit 10. Normal update-before-payment pays 10; delayed assignment allows three total payouts via two nested callbacks, paying 30. |
| Faulty access control | `fund` | Toy treasury 100 HSK. Authorized actor pays fixed beneficiary 5; bypassed checks allow an unauthorized actor to pay arbitrary recipient 40. |
| Price manipulation | `exactInputSingle` | Toy pool 1,000 HSK / 100,000 USDT, linked to a toy lender. Normal borrowing uses self-funded 100 HSK collateral and independent price 100 to borrow 5,000. The attack instead uses flash funding and the changed pool spot price. |

The normal price specimen intentionally differs in funding and oracle source; it is an explanatory comparator, not a controlled one-variable experiment. Both retain position owner, collateral, outstanding debt, LTV, price source and checks.

## Price accounting and wording

The attack borrows 100,000 USDT from the flash provider, buys 500 HSK, pledges 100 HSK, and borrows 30,000 USDT using a marginal pool price of 400 and maximum LTV 75%. Selling the remaining 400 HSK returns 88,888.888888 USDT (rounded down to six decimals), leaving 900 HSK / 111,111.111112 USDT in the pool. Repayment is 100,090 USDT.

The actor retains **18,798.888888 USDT cash**, a collateral claim to 100 HSK and **30,000 USDT debt**. The cash is not labelled net profit. No default or liquidation is simulated. The independent reference price of 100 is an explicit toy assumption; it values the collateral at 10,000 USDT, below debt by 20,000. This is a valuation gap, not a realized liquidation loss. Final pool price is about 123.456790124444, not 100.

Physical USDT changes are actor +18,798.888888, pool +11,111.111112, lender −30,000 and flash provider +90; they sum to zero. The pool loses 100 HSK and lender custody gains the same 100 HSK. The borrower's collateral claim and lender custody refer to the same tokens.

## Generation and execution boundary

The authoring generator takes `INPUT_TRANSACTIONS_JSON OUTPUT_CASES_JSON` as positional arguments and uses only the Python standard library. It reads the merged source, selects the three fixed transaction hashes, preserves snapshots and writes six deterministic specimens. It makes no network requests or model calls. `model_result` remains null until a separately authorized detector run provides actual results. A null result means no detector inference has been run.
