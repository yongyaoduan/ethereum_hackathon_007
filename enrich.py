"""Archive complete per-transaction evidence, with resumable pagination."""
import json
import concurrent.futures
import urllib.parse
from pathlib import Path
from collect import get

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/evidence';OUT.mkdir(exist_ok=True)
CONTRACTS=ROOT/'data/contracts';CONTRACTS.mkdir(exist_ok=True)

def contract(addr):
    p=CONTRACTS/(addr.lower()+'.json')
    if not p.exists():p.write_text(json.dumps(get('/api/v2/smart-contracts/'+addr),ensure_ascii=False,indent=2))
    return json.loads(p.read_text())

def pages(path):
    items=[];query={}
    while True:
        d=get(path+('?' + urllib.parse.urlencode(query) if query else ''))
        items.extend(d['items']);query=d.get('next_page_params')
        if not query:return items

def enrich(tx):
    p=OUT/(tx['hash']+'.json')
    if p.exists():return json.loads(p.read_text())
    base='/api/v2/transactions/'+tx['hash']
    d={'transaction':get(base),'logs':pages(base+'/logs'),'internal_transactions':pages(base+'/internal-transactions'),'token_transfers':pages(base+'/token-transfers'),'pagination_complete':True,'source':'https://hsk.blockscout.com'+base}
    to=d['transaction'].get('to')
    if to and to.get('is_verified'):
        c=contract(to['hash'])
        d['contract_address']=to['hash']
        d['contract_name']=c.get('name')
        d['contract_verified']=c.get('is_verified')
        d['implementations']=c.get('implementations',[])
        for impl in d['implementations']:contract(impl['address_hash'])
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d

if __name__=='__main__':
    rows=[]
    for name in ['0xB210D2120d57b758EE163cFfb43e73728c471Cf1','0xf1b50ed67a9e2cc94ad3c477779e2d4cbfff9029']:
        d=json.loads((ROOT/'data'/f'{name}.json').read_text())
        # Development only. Freeze random final set separately.
        count={}
        for tx in d['items']:
            m=tx.get('method');count[m]=count.get(m,0)+1
            if count[m]<=4:rows.append(tx)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for d in pool.map(enrich,rows):print(d['transaction']['hash'],d['transaction'].get('method'),len(d['logs']),flush=True)
