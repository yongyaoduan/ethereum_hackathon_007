"""Freeze reference decisions before any inference on the random evaluation set."""
import json,hashlib
from pathlib import Path
from features import state
from taxonomy import build
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
ALL=[x['id'] for x in build()[0]]
rows=[]
for t in json.loads((DATA/'random-refresh/frozen-200.json').read_text())['transactions']:
 d=json.loads((DATA/'evidence'/(t['hash']+'.json')).read_text());tx=d['transaction'];m=tx.get('method');events=[(l.get('decoded') or {}).get('method_call','').split('(')[0] for l in d['logs']]
 assert d['pagination_complete']
 expected=[];unassessed=[];basis=''
 if (tx.get('raw_input') or '')[:10] in ['0x3db6be2b','0x440a5e20']:
  assert tx['from']['hash'].lower()=='0xdeaddeaddeaddeaddeaddeaddeaddeaddead0001'
  assert tx['to']['hash'].lower()=='0x4200000000000000000000000000000000000015'
  assert int(tx['value'])==0 and not d['logs'] and not d['token_transfers']
  assert all(x.get('type')=='delegatecall' and int(x.get('value') or 0)==0 for x in d['internal_transactions'])
  basis='L1Block system predeploy update from the protocol depositor, with zero value, no logs/token movements and only a delegatecall. Selector matches setL1BlockValuesEcotone() or setL1BlockValuesJovian() by Keccak. Ecotone target verified; Jovian target unverified, interpretation additionally relies on standard OP predeploy/address/caller/input semantics, not source equivalence. No supported economic action.'
 elif m=='fund':
  assert 'Funded' in events and 'NativeReceived' in events
  expected=[];unassessed=['deposit','claim']
  basis='Verified Treasury fund authorizes a native payment to a factory-recognized subaccount; Funded and NativeReceived with native trace. No deposit accounting or prior reward entitlement is established by this evidence. Deposit/Claim remain unassessed pending subaccount/business-context verification; not automatically negative.'
 elif m in ['setPrice','setPriceForArbitrum','verifyOracleProofV2']:
  assert not d['token_transfers'] and int(tx['value'])==0
  basis='Verified executed PriceFeed/SupraOraclePull implementation updates oracle price/gas data; successful receipt, no asset movement. This is neither loan interest accrual nor execution of an asset bridge.'
 elif m=='transmit':
  assert set(events)<=set(['UsdPerUnitGasUpdated','Transmitted']) and not d['token_transfers']
  basis='CommitStore report contains gas-price updates and Transmitted only. No asset bridging, auction/name commit-reveal or interest update occurred. Contract name CommitStore alone is not the Commit economic action.'
 elif m=='confirmMerge':
  assert 'PositionsMerged' in events and 'PaidOut' in events
  expected=['redeem'];unassessed=['withdraw','unlock']
  basis='Verified PredictionMarket confirmMerge consumes complementary investment shares, releases backing, and pays native HSK via Treasury; PositionsMerged, PaidOut and native traces agree. Redeem includes investment shares recorded in storage. Generic Withdraw/Unlock overlap is not scored for this case.'
 elif m=='batchSettle':
  assert 'SettlementPaid' in events and 'PaidOut' in events
  unassessed=['redeem','refund','claim','withdraw']
  basis='Verified PredictionMarket batchSettle extinguishes outcome holdings and pays native HSK. Its code handles both resolved and voided events, but historical resultType is not supplied, so redemption/refund/claim/withdraw interpretation remains unassessed. Do not invent a positive reference.'
 elif m=='claimReward':
  assert 'RewardClaimed' in events
  assert any(int(c.get('value') or 0)>0 and (c.get('to') or {}).get('hash','').lower()==tx['from']['hash'].lower() and c.get('success') for c in d['internal_transactions'])
  expected=['claim']
  basis='Successful claimReward with indexed user/position and positive RewardClaimed amount, RewardPoolUpdated, plus actual native payment to caller. The destination is not source-verified, so proof relies on decoded reward event and matching payout rather than guessed contract name.'
 else:
  unassessed=ALL[:]
  basis='No reviewed, unambiguous reference rule for this function. Retain this random sample and model output, but do not fabricate ground truth for any label.'
 rows.append({'id':tx['hash'],'split':'random_final_refresh','expected':expected,'unassessed':unassessed,'basis':basis,'state':state(d)})
out=DATA/'random-refresh-reference-200-v1.json'
if out.exists():raise SystemExit('Reference already frozen; version changes explicitly instead of overwrite')
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2))
manifest={'n':len(rows),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'fully_assessed_transactions':sum(not r['unassessed'] for r in rows),'partially_assessed_transactions':sum(0<len(r['unassessed'])<45 for r in rows),'wholly_unassessed_transactions':sum(len(r['unassessed'])==45 for r in rows),'positive_counts':{k:sum(k in r['expected'] for r in rows) for k in ALL},'notes':'No model predictions were inspected for these 200 transactions. Some references are evidence-qualified; see each basis. This is not an Etherscan-provided gold set.'}
(DATA/'random-refresh-reference-manifest-v1.json').write_text(json.dumps(manifest,indent=2))
print({k:v for k,v in manifest.items() if k!='positive_counts'})
