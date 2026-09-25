import json
from pathlib import Path
from collections import defaultdict
from enrich import enrich,contract
ROOT=Path(__file__).resolve().parent;D=ROOT/'data';groups=defaultdict(dict)
for p in sorted((D/'missing-class-search').glob('marketplace-[0-9]*.json')):
 for t in json.loads(p.read_text())['items']:
  if t.get('method') in ['purchaseListing','makeOffer','acceptOffer','cancelOffer'] and t.get('status')=='ok':groups[t['method']][t['hash']]=t
plan=[t for m,r in sorted(groups.items()) for t in sorted(r.values(),key=lambda t:t['hash'])[:6]]
(D/'marketplace-candidate-plan.json').write_text(json.dumps(plan,indent=2));errors=[]
for i,t in enumerate(plan):
 try:
  d=enrich(t)
  for c in d['internal_transactions']:
   if c.get('type')=='delegatecall' and c.get('success') and (c.get('to') or {}).get('is_verified'):contract(c['to']['hash'])
  print(i+1,len(plan),t['method'],t['hash'],[(l.get('decoded') or {}).get('method_call','?').split('(')[0] for l in d['logs']],flush=True)
 except Exception as e:errors.append({'id':t['hash'],'error':str(e)})
(D/'marketplace-candidate-errors.json').write_text(json.dumps(errors,indent=2))
