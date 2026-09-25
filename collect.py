"""Read-only candidate discovery. Search hits never serve as reference labels."""
import concurrent.futures
import json
import time
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from taxonomy import build

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'data/discovery';OUT.mkdir(exist_ok=True)
BASE='https://hsk.blockscout.com'
LOCK=threading.Lock()
NEXT_REQUEST=0.0

def get(path):
    global NEXT_REQUEST
    for attempt in range(6):
        try:
            with LOCK:
                delay=max(0,NEXT_REQUEST-time.monotonic())
                if delay:time.sleep(delay)
                NEXT_REQUEST=time.monotonic()+1.1
            req=urllib.request.Request(BASE+path,headers={'User-Agent':'WalletResearch/1.0'})
            with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504) or attempt==5:raise
            try:delay=float(e.headers.get('Retry-After','15'))
            except ValueError:delay=15
            with LOCK:NEXT_REQUEST=max(NEXT_REQUEST,time.monotonic()+max(delay,2**attempt))
        except Exception as e:
            if attempt==5:raise
            time.sleep(min(2**attempt,16))

def find(row):
    path=OUT/(row['id']+'.json')
    if path.exists():return json.loads(path.read_text())
    # Registry search may return only one overload; empty results are not absence proofs.
    name=row['label'].replace(' ','')
    name=name[0].lower()+name[1:]
    result={'label':row['label'],'search_name':name,'retrieved_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source':BASE,'candidates':[],'coverage_note':'Name search is incomplete and may return a default selector not used on this chain. It is candidate discovery, not action proof.'}
    try:
        methods=get('/api/v2/advanced-filters/methods?'+urllib.parse.urlencode({'q':name}))
        result['methods']=methods
        for method in methods:
            selector=method['method_id']
            data=get('/api/v2/advanced-filters?'+urllib.parse.urlencode({'methods':selector}))
            result['candidates'].extend(data.get('items',[]))
            result['next_page_params']=data.get('next_page_params')
    except Exception as e:result['error']=str(e)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':
    labels,_=build()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for r in pool.map(find,labels):
            print(r['label'],len(r['candidates']),r.get('error',''),flush=True)
    allrows=[json.loads(p.read_text()) for p in OUT.glob('*.json')]
    unique={x.get('hash',x.get('transaction_hash')) for r in allrows for x in r['candidates']}
    print('Unique candidate hashes',len(unique),flush=True)
