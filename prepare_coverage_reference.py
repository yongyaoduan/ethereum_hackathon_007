"""Evidence-gated references for reviewed action semantics; no model predictions."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from features import state
from taxonomy import build
ROOT=Path(__file__).resolve().parent;DATA=ROOT/'data'
ALL=[x['id'] for x in build()[0]]
plans=json.loads((DATA/'coverage-candidate-plan.json').read_text())['transactions']+json.loads((DATA/'extra-candidate-plan.json').read_text())
rows=[];unresolved=[]
for t in {t['hash']:t for t in plans}.values():
 p=DATA/'evidence'/(t['hash']+'.json')
 if not p.exists():continue
 d=json.loads(p.read_text());tx=d['transaction'];m=tx.get('method');s=state(d)
 events=[(x.get('decoded') or {}).get('method_call','').split('(')[0] for x in d['logs']];ev=set(events)
 verified=[c for c in s['contracts'] if c.get('verified') and c.get('source_excerpt')]
 tags=set();unknown=set();basis='';native_refund=False
 if tx['status']!='ok':basis='Transaction reverted; no completed economic actions survive. Receipt status and logs checked.'
 elif not verified:
  unresolved.append({'id':tx['hash'],'method':m,'reason':'Executed function source absent/unverified; retain candidate for further audit, not a fabricated gold label.'});continue
 elif m in ['addLiquidity','addLiquidityETH'] and 'Mint' in ev and d['token_transfers']:
  tags.add('add_liquidity');basis='Reviewed AMM router source, pool Mint/Sync and constituent/LP transfers prove adding liquidity.'
  if 'PairCreated' in ev:tags.add('create')
  native_refund=True
 elif m in ['removeLiquidity','removeLiquidityETH','removeLiquidityETHWithPermit'] and 'Burn' in ev and d['token_transfers']:
  tags.add('remove_liquidity');basis='AMM router exit with pool Burn/Sync, LP receipt burn and constituent payouts. Auxiliary Burn excluded.'
  if m=='removeLiquidityETHWithPermit':tags.add('approve')
 elif m in ['exactInputSingle','swapExactETHForTokens','swapExactTokensForETH'] and 'Swap' in ev and len(d['token_transfers'])>=2:
  tags.add('swap');basis='Reviewed swap router, pool Swap event and distinct asset transfers establish actual exchange.'
 elif m=='ccipSend' and ev.intersection(['CCIPMessageSent','CCIPSendRequested']) and ev.intersection(['LockedOrBurned','Burned']) and d['token_transfers']:
  tags.add('bridge');basis='Verified CCIP Router transfers message tokenAmounts to cross-chain token pools, followed by LockedOrBurned and CCIP message event. Native fee wrapping is separately visible; allowance consumption is not Approve.'
 elif m=='batchCancelListings' and 'ListingCancelled' in ev:
  tags.add('cancel');basis='Verified marketplace deactivates active seller listing and returns its escrowed NFT; ListingCancelled and NFTReturnedToSeller. No sale or payment refund occurred.'
  unknown.add('unlock')
 elif m=='batchTogglePendingWithdrawal' and 'PendingWithdrawalToggled' in ev:
  basis='Verified AssetVault only toggles a pending withdrawal pause flag. It does not cancel the request, restore a balance, initiate a new request, or execute payment. Cancel Withdrawal is false.'
 elif m=='vote' and d.get('contract_name')=='RubyscoreVote' and not d['logs'] and not d['token_transfers']:
  basis='Verified RubyscoreVote vote() is an empty payable function, with no governance proposal or vote recorded. Method name does not prove the Vote label.'
 elif m=='stakeLocked' and 'Stake' in ev:
  tags.update(['stake','lock']);basis='Verified HashKeyChainStaking accepts native stake, mints auxiliary staking shares, writes a fixed-duration lock and emits Stake including lockEndTime. Explicit lock term supports Lock; receipt issuance is not Mint.'
 elif m=='approve' and 'Approval' in ev:
  tags.add('approve');basis='Explicit approve call and matching Approval event; not allowance consumption.'
 elif m in ['batchMint','mint'] and d.get('contract_name') in ['CustomNFT','PizzaDayNFT'] and 'Transfer' in ev:
  assert any((x.get('from') or {}).get('hash','').lower()=='0x'+'0'*40 for x in d['token_transfers'])
  tags.add('mint');basis='Reviewed NFT mint function, successful receipt and NFT issuance from zero address.'
 elif m=='borrowDebt' and 'BorrowDebt' in ev:
  tags.add('borrow');basis='Historical LendingPool delegate source, BorrowDebt event and actual user/fee token payouts. Cross-chain branch absent.'
 elif m=='claim' and d.get('contract_name')=='Stake' and 'RewardClaimed' in ev and d['token_transfers']:
  tags.add('claim');basis='Reviewed earned staking reward payout, RewardClaimed and real token transfers; staking principal is not removed.'
 elif m=='deploy' and 'ContractDeployed' in ev:
  tags.add('deploy');basis='Reviewed factory contract instantiation, ContractDeployed and successful EVM creation trace. Not an independent protocol record Create.'
 elif m in ['createPool','createMarket','createSubAccount'] and ev.intersection(['NewPool','PoolCreated','MarketCreated','SubAccountCreated']):
  tags.add('create');basis='Reviewed creation of a distinct protocol pool/market/subaccount, matching event; deployment counted separately only with successful creation trace.'
  if m=='createPool' and d.get('contract_name')=='Stake':unknown.add('deposit')
 elif m=='supplyCollateral' and 'SupplyCollateral' in ev and d['token_transfers']:
  tags.add('collateralize');basis='Reviewed collateral supply, SupplyCollateral and actual pledged token movement. An auxiliary position record is not another Create action.'
 elif m=='supplyLiquidity' and 'SupplyLiquidity' in ev and d['token_transfers']:
  tags.add('supply');basis='Reviewed lending supply and lending-share issuance, SupplyLiquidity with transfers. This is not AMM liquidity or independent Mint.'
 elif m=='repayWithSelectedToken' and 'RepayByPosition' in ev and d['token_transfers']:
  tags.add('repay');basis='Reviewed debt repayment and RepayByPosition; actual input asset payment. Secondary swap/interest assessed from actual events.'
  if 'DODOSwap' in ev:tags.add('swap')
  if 'Approval' in ev:unknown.add('approve')
 elif m=='setInterestRateModel' and 'InterestRateModelSet' in ev:
  tags.add('update_interest');basis='Actual lending interest-rate model change, verified executed setter and InterestRateModelSet event.'
 elif m=='requestWithdraw' and 'WithdrawalAdded' in ev:
  if 'WithdrawExecuted' in ev:tags.add('withdraw')
  else:tags.add('initiate_withdrawal')
  basis='Reviewed AssetVault requestWithdraw branch: WithdrawalAdded without execution is pending; WithdrawExecuted plus payout in the same transaction is immediate Withdraw.'
 elif m=='executeExpiredPendingWithdrawal' and 'WithdrawExecuted' in ev:
  tags.add('complete_withdrawal');basis='Verified AssetVault checks a pre-existing pending request and challenge-period expiry, then pays and emits WithdrawExecuted.'
 elif m=='requestUnstakeFlexible' and 'RequestUnstakeFlexible' in ev:
  tags.update(['unstake','initiate_withdrawal']);basis='Verified staking exit burns shares, reduces staked principal and adds a pending withdrawal with claimableBlock; no immediate HSK payout.'
  unknown.add('initiate_redemption')
 elif m=='stake' and ev.intersection(['Staked','PositionCreated']):
  tags.add('stake');basis='Verified staking entry, positive principal and Staked/PositionCreated. Reward accounting alone is not Update Interest.'
  if 'PositionCreated' in ev:unknown.add('lock')
 elif m=='unlock' and 'Unlock' in ev and d['token_transfers']:
  tags.add('unlock');basis='Verified EarnHSK lock record is checked for maturity, principal returned, lock marked withdrawn, Unlock emitted.'
  unknown.update(['unstake','withdraw'])
 elif m=='unstake' and ev.intersection(['Unstaked','PositionUnstaked']):
  tags.add('unstake');basis='Verified staking exit reduces staked balance and sends principal; reward claim separately evidenced where positive.'
  if 'RewardClaimed' in ev and any(int(p['value'])>0 for l in d['logs'] if (l.get('decoded') or {}).get('method_call','').startswith('RewardClaimed(') for p in l['decoded']['parameters'] if p['name'] in ['amount','reward']) and (d['token_transfers'] or any(int(x.get('value') or 0)>0 for x in d['internal_transactions'])):tags.add('claim')
  unknown.add('unlock')
 elif m=='unstakeLocked' and 'Unstake' in ev:
  tags.add('unstake');basis='Verified HashKeyChainStaking unstakeLocked burns staking receipts, reduces principal, and sends HSK; Unstake and native payout observed.'
  unknown.update(['unlock','redeem'])
 elif m=='registerMerchant' and 'MerchantRegistered' in ev:
  tags.add('register');basis='Verified TegataFactory registers merchant and deploys/initializes a settlement wrapper; registration event and execution trace agree.'
 elif m=='withdrawCollateral' and 'WithdrawCollateral' in ev and d['token_transfers']:
  tags.add('de_collateralised');basis='Reviewed lending collateral release and WithdrawCollateral with actual token outflow; use specific collateral release action.'
 elif m=='withdrawLiquidity' and 'WithdrawLiquidity' in ev and d['token_transfers']:
  tags.add('withdraw');unknown.add('redeem');basis='Lending liquidity withdrawal with WithdrawLiquidity and payout; receipt-redemption overlap remains unassessed.'
 else:
  unresolved.append({'id':tx['hash'],'method':m,'reason':'No reviewed reference rule yet; candidate preserved.'});continue
 if tx['status']=='ok':
  if 'InterestAccrued' in ev:tags.add('update_interest')
  creates=[x for x in d['internal_transactions'] if x.get('type') in ['create','create2'] and x.get('success')]
  if creates:tags.add('deploy')
  # Wrapper overlap requires a known WHSK event emitter, not any Deposit event.
  for log in d['logs']:
   if log['address']['hash'].lower()!='0xb210d2120d57b758ee163cffb43e73728c471cf1':continue
   event=(log.get('decoded') or {}).get('method_call','').split('(')[0]
   if event=='Deposit':tags.update(['wrap','deposit'])
   if event=='Withdrawal':tags.update(['unwrap','withdraw'])
  if native_refund and any(c.get('success') and c.get('type')=='call' and int(c.get('value') or 0)>0 and (c.get('from') or {}).get('hash','').lower()==tx['to']['hash'].lower() and (c.get('to') or {}).get('hash','').lower()==tx['from']['hash'].lower() for c in d['internal_transactions']):tags.add('refund')
 assert not(tags&unknown)
 rows.append({'id':tx['hash'],'method':m,'contract':d.get('contract_name'),'block':tx['block_number'],'expected':sorted(tags),'unassessed':sorted(unknown),'basis':basis,'state':s})
(DATA/'coverage-reference-draft.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
(DATA/'coverage-reference-unresolved.json').write_text(json.dumps(unresolved,ensure_ascii=False,indent=2))
print('References drafted',len(rows),'Unresolved',len(unresolved));print(Counter(k for r in rows for k in r['expected']))
