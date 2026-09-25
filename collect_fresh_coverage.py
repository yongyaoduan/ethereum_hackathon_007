import json
from pathlib import Path
from collections import defaultdict
from enrich import enrich,contract
ROOT=Path(__file__).resolve().parent;D=ROOT/'data'
methods=set('addLiquidityETH approve batchMint borrowDebt claim createMarket createPool createSubAccount deploy exactInputSingle executeExpiredPendingWithdrawal mint registerMerchant removeLiquidity removeLiquidityETH removeLiquidityETHWithPermit repayWithSelectedToken requestUnstakeFlexible requestWithdraw setInterestRateModel stake supplyCollateral supplyLiquidity unlock unstake unstakeLocked vote withdrawCollateral withdrawLiquidity swapExactETHForTokens swapExactTokensForETH ccipSend batchCancelListings stakeLocked deposit withdraw makeOffer purchaseListing acceptOffer cancelOffer'.split())
seen={json.loads(line)['id'] for p in (ROOT/'runs').glob('*/results.jsonl') for line in p.read_text().splitlines() if line.strip()}
# All first-round IDs are retired, including requests rejected by the service.
seen.update(r['id'] for r in json.loads((D/'coverage-final-v1.json').read_text()))
seen.update(json.loads((D/'random/frozen-200.json').read_text())['hashes'])
seen.update(json.loads((D/'random-refresh/frozen-200.json').read_text())['hashes'])
paths=list((D/'protocol-discovery').glob('0x*.json'))+list((D/'missing-class-search').glob('marketplace-[0-9]*.json'))+[D/'0xB210D2120d57b758EE163cFfb43e73728c471Cf1.json',D/'0xf1b50ed67a9e2cc94ad3c477779e2d4cbfff9029.json']
groups=defaultdict(dict)
for p in paths:
 if not p.exists():continue
 for t in json.loads(p.read_text()).get('items',[]):
  if t['hash'] not in seen and t.get('method') in methods and t.get('status')=='ok':groups[t['method']][t['hash']]=t
planpath=D/'fresh-coverage-candidate-plan.json'
if planpath.exists():plan=json.loads(planpath.read_text())
else:
 plan=[t for m,g in sorted(groups.items()) for t in sorted(g.values(),key=lambda t:t['hash'])[:3]]
 planpath.write_text(json.dumps(plan,indent=2))
errors=[]
for i,t in enumerate(plan):
 try:
  d=enrich(t)
  for c in d['internal_transactions']:
   if c.get('type')=='delegatecall' and c.get('success') and (c.get('to') or {}).get('is_verified'):contract(c['to']['hash'])
  print(i+1,len(plan),t['method'],t['hash'],[(l.get('decoded') or {}).get('method_call','?').split('(')[0] for l in d['logs']],flush=True)
 except Exception as e:errors.append({'id':t['hash'],'error':str(e)})
(D/'fresh-coverage-candidate-errors.json').write_text(json.dumps(errors,indent=2))
