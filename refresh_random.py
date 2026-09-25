"""Fresh 200 unseen transactions from the original random-block pool; no label filters."""
import json,random,hashlib,sys
from pathlib import Path
from enrich import enrich
ROOT=Path(__file__).resolve().parent;D=ROOT/'data';out=D/'random-refresh';out.mkdir(exist_ok=True)
plan=out/'frozen-200.json'
if not plan.exists():
 pool={t['hash']:t for p in (D/'random').glob('block-*.json') for t in json.loads(p.read_text())['items']}
 seen={json.loads(line)['id'] for p in (ROOT/'runs').glob('*/results.jsonl') for line in p.read_text().splitlines() if line.strip()}
 # Include the full retired set, even a service-rejected transaction.
 seen.update(json.loads((D/'random/frozen-200.json').read_text())['hashes'])
 available=sorted(set(pool)-seen);seed=260926194
 chosen=random.Random(seed).sample(available,200)
 result={'seed':seed,'available_count':len(available),'hashes':chosen,'transactions':[pool[h] for h in chosen],'design':'Uniform sample without replacement from the remaining unseen transactions in the pre-existing 400-random-block pool. No method, outcome, or label filtering. Shares block/protocol clusters with the retired first round; not claimed independent at block/contract level.','retirement':'Original 200 exposed for error analysis after random macro BA=75%. Keep their result unchanged; this replacement set is frozen before any inference.'}
 plan.write_text(json.dumps(result,indent=2))
rows=json.loads(plan.read_text())['transactions'];part=int(sys.argv[1]) if len(sys.argv)>1 else 0
errors=[]
for i,t in enumerate(rows[part::2]):
 try:enrich(t)
 except Exception as e:errors.append({'id':t['hash'],'error':str(e)})
 if (i+1)%10==0:print('part',part,i+1,'/100','errors',len(errors),flush=True)
(out/f'errors-{part}.json').write_text(json.dumps(errors,indent=2))
