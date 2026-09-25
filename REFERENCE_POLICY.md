# Action reference policy

Scope is the 45 unique names actually captured from Etherscan By Actions. These are our explicit operational definitions; Etherscan does not publish its entire classifier implementation.

## Transaction scope

One successful transaction may execute several distinct actions. Count a secondary swap, a new pool's deployment, and an explicit allowance grant when evidenced by execution. Do not turn every accounting mutation into another user action.

- Failed transactions: no completed action.
- Token allowance consumption is not Approve, even if it emits Approval.
- Auxiliary receipt token mint/burn is not Mint/Burn.
- A protocol pool/market/account created through a factory may be Create + Deploy. A factory deploying an implementation/interest-rate-model alone is Deploy. Ordinary position/accounting records created as part of Stake/Supply/Borrow are not independently Create.
- Prefer the specific exit action: Unstake, Remove Liquidity, De-collateralised, Redeem or Complete Withdrawal. Do not automatically add generic Withdraw for the same movement. Wrap + Deposit and Unwrap + Withdraw are explicitly allowed exceptions carried forward from v2.
- Unlock requires evidence of releasing a lock; ordinary stake exit alone does not imply another Unlock. Stake may coexist with Lock when a separately evidenced explicit lock duration exists; ambiguous overlap is left unassessed.
- For queued withdrawal, distinguish still pending, immediate completion in the initiating transaction, and completion of an earlier queued request.
- Interest update is actual debt interest accrual/rate-model change. Staking reward accounting, exchange rates and oracle price/gas updates are not Update Interest.

## Evidence and uncertainty

Reference rules require successful receipts, full paginated logs/transfers/internal calls, and protocol semantics. Method strings only retrieve candidates. Match proxy source to the delegate target actually used by the historical transaction. Current proxy metadata is not historical proof.

If a reference decision cannot be resolved (e.g. a refund branch needs historical state), list that label in `unassessed`. Such decisions never become negatives. Publish how many transactions and labels are fully/partially assessed. Unknown references remain in the original random sample. Never silently replace them.

Do not tune prompts or thresholds on final results. Development and final cases are separate; report shared protocol-family overlap explicitly when independent families are unavailable.
