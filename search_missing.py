import json,urllib.parse
from pathlib import Path
from collections import Counter
from collect import get
ROOT=Path(__file__).resolve().parent/'data';OUT=ROOT/'missing-class-search';OUT.mkdir(exist_ok=True)
addresses={
 'marketplace':'0x5d6C18a0f9E63B48a556394a6429dc5b035c9ec0',
 'factory-governor':'0xE34653590b5846f20c1a361B1D0bf1bF67206fF9',
 'liquidity-locker':'0x2ec80BbaAB0A9F9C6c5de35808D39da34755467B',
 'safe-migration':'0x6439e7ABD8Bb915A5263094784C5CF561c4172AC',
}
for name,address in addresses.items():
 params={};seen={};limit=200 if name=='marketplace' else 2
 for i in range(limit):
  p=OUT/f'{name}-{i}.json'
  if p.exists():d=json.loads(p.read_text())
  else:
   d=get('/api/v2/addresses/'+address+'/transactions'+('?' + urllib.parse.urlencode(params) if params else ''));p.write_text(json.dumps(d,indent=2))
  for t in d['items']:seen[t['hash']]=t
  params=d.get('next_page_params')
  if not params:break
 summary={'address':address,'transactions':len(seen),'exhausted':not params,'next_page_params':params,'methods':dict(Counter(t.get('method') for t in seen.values()))}
 (OUT/f'{name}-summary.json').write_text(json.dumps(summary,indent=2));print(name,summary,flush=True)
