import json,hashlib
from pathlib import Path
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent;P=ROOT/'data'
rows=json.loads((P/'coverage-reference-draft.json').read_text())
base=json.loads((P/'development-diverse-v3.json').read_text());known={r['id'] for r in base}
# Keep every previously exposed model case in development.
dev={r['id']:r for r in base};remaining=[r for r in rows if r['id'] not in known]
groups=defaultdict(list)
for r in remaining:groups[(r['method'],r['contract'])].append(r)
counts=Counter(k for r in remaining for k in r['expected'])
for key,group in sorted(groups.items(),key=lambda p:str(p[0])):
 if len(group)<3:continue
 r=min(group,key=lambda x:(x['block'],x['id']))
 if any(counts[k]<=1 for k in r['expected']):continue
 dev[r['id']]=r
 for k in r['expected']:counts[k]-=1
held=[r for r in remaining if r['id'] not in dev]
for r in dev.values():r['split']='development'
for r in held:r['split']='coverage_final'
for name,values in [('development-diverse-v4.json',list(dev.values())),('coverage-final-v1.json',held)]:
 path=P/name
 if path.exists():raise SystemExit('Already frozen: '+name)
 path.write_text(json.dumps(values,ensure_ascii=False,indent=2))
manifest={'split_rule':'Existing exposed cases remain development; oldest case per method/contract-name group with >=3 candidates can join development if at least one held-out positive remains for every label in that case. Others held out.','limitations':'Shared protocol implementations across splits remain: limited HSK coverage prevents universal contract-family isolation. This is not a cross-protocol generalization estimate. Some singleton labels appear only in held-out set.','development_n':len(dev),'held_out_n':len(held),'held_out_positive_counts':dict(Counter(k for r in held for k in r['expected'])),'files':{name:hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ['development-diverse-v4.json','coverage-final-v1.json']}}
(P/'coverage-split-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
