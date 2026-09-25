import json
from collections import defaultdict
from enrich import ROOT,enrich
methods=set('ccipSend batchCancelListings burn claimRoyalties removeLiquidityETH removeLiquidityETHWithPermit stakeLocked release buyTokens sellTokens createAndLaunch createComplianceToken createLendingPool batchTogglePendingWithdrawal multicall'.split())
rows=defaultdict(dict)
for p in sorted((ROOT/'data/protocol-discovery').glob('0x*.json')):
 for t in json.loads(p.read_text())['items']:
  if t.get('method') in methods:rows[t['method']][t['hash']]=t
plan=[t for m,r in sorted(rows.items()) for t in sorted(r.values(),key=lambda t:t['hash'])[:3]]
(ROOT/'data/extra-candidate-plan.json').write_text(json.dumps(plan,indent=2))
for i,t in enumerate(plan):
 try:
  d=enrich(t);print(i+1,len(plan),t['method'],t['hash'],[(l.get('decoded') or {}).get('method_call','?').split('(')[0] for l in d['logs']],flush=True)
 except Exception as e:print(t['hash'],'ERROR',str(e),flush=True)
