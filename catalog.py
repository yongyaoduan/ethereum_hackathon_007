"""Discover protocol families and candidate histories; names are not action labels."""
import json,re,urllib.parse
from pathlib import Path
from collect import get
ROOT=Path(__file__).resolve().parent/'data'
OUT=ROOT/'protocol-discovery';OUT.mkdir(exist_ok=True)

def cached(path,file):
    if file.exists():return json.loads(file.read_text())
    d=get(path);file.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d

if __name__=='__main__':
    items=[];params={};exhausted=False
    for i in range(40):
        d=cached('/api/v2/smart-contracts'+('?' + urllib.parse.urlencode(params) if params else ''),OUT/f'verified-{i}.json')
        items+=d['items'];params=d.get('next_page_params')
        if not params:exhausted=True;break
    (ROOT/'verified-catalog.json').write_text(json.dumps(items,indent=2))
    (OUT/'catalog-status.json').write_text(json.dumps({'n':len(items),'exhausted':exhausted,'next_page_params':params},indent=2))
    print('Catalog',len(items),'exhausted',exhausted,flush=True)
    selected=[]
    for r in items:
        a=r['address'];name=(a.get('name') or '')+' '+str(a.get('implementations') or [])
        if re.search(r'Stak|Vault|Router|Factory|Lock|Hns|Morpho|Market|NFT|Vote|Auction|Lending|Reward|Vesting|Seaport|Registrar|Controller|Bond|Escrow',name,re.I) and (r.get('transactions_count') or 0)>0:selected.append(a)
    for a in selected:
        try:
            d=cached('/api/v2/addresses/'+a['hash']+'/transactions',OUT/(a['hash']+'.json'))
            print(a['name'],a['hash'],sorted(set(str(t.get('method')) for t in d['items'])),flush=True)
        except Exception as e:print(a['hash'],'ERROR',str(e),flush=True)
