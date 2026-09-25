"""Reproducible cluster sample: random blocks, complete transaction lists, then 200 txs.

Freeze block plan and tx IDs before labeling or model inference. Do not filter out
system transactions, failures, empty-input transfers or unsupported actions.
"""
import concurrent.futures
import hashlib
import json
import random
import time
import urllib.parse
from pathlib import Path
from collect import get

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/random';OUT.mkdir(exist_ok=True)
SEED=260926177
END=28003134 # Observed real head on HSK before sampling, not a guessed future block.
START=END-90*24*60*60//2

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def block(n):
    p=OUT/f'block-{n}.json'
    if p.exists():return json.loads(p.read_text())
    items=[];params={};pages=0
    while True:
        data=get('/api/v2/blocks/'+str(n)+'/transactions'+('?' + urllib.parse.urlencode(params) if params else ''))
        items.extend(data['items']);pages+=1
        params=data.get('next_page_params')
        if not params:break
    result={'block':n,'items':items,'pages':pages,'complete':True}
    save(p,result);return result

if __name__=='__main__':
    planpath=OUT/'plan.json'
    if planpath.exists():plan=json.loads(planpath.read_text())
    else:
        plan={'seed':SEED,'block_start':START,'block_end':END,'block_count':400,'sample_size':200,'design':'Uniformly sample 400 blocks without replacement, collect every transaction with full pagination, then uniformly sample 200 unique hashes. Cluster-based sample; not claimed to be an exactly uniform all-chain transaction sample. Includes system transactions.','blocks':sorted(random.Random(SEED).sample(range(START,END+1),400))}
        save(planpath,plan)
    rows=[];fail=[]
    def safe(n):
        try:return block(n)
        except Exception as e:return {'block':n,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,r in enumerate(pool.map(safe,plan['blocks'])):
            if 'error' in r:fail.append(r)
            else:rows.extend(r['items'])
            if (i+1)%20==0:print('Blocks',i+1,'txs',len(rows),'errors',len(fail),flush=True)
    save(OUT/'errors.json',fail)
    if fail:raise SystemExit('Incomplete block sample. Rerun cached plan; do not silently drop failed blocks.')
    pool={x['hash']:x for x in rows}
    chosen=random.Random(SEED+1).sample(sorted(pool),200)
    result={'plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),'pool_count':len(pool),'hashes':chosen,'transactions':[pool[h] for h in chosen]}
    target=OUT/'frozen-200.json'
    if target.exists():
        assert json.loads(target.read_text())==result,'Refusing to replace frozen sample'
    else:save(target,result)
    print('Frozen 200 of',len(pool),'SHA256',hashlib.sha256(target.read_bytes()).hexdigest(),flush=True)
