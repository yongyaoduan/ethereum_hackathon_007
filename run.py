"""One Jev request per transaction; all 45 independent actions; no persisted key."""
import argparse
import getpass
import hashlib
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from evaluate import metrics
from compact import compact_state

ROOT=Path(__file__).resolve().parent

def classify(state,questions,key):
    payload={'model':'typesafe/jev-1.13','state':state,'questions':questions}
    req=urllib.request.Request('https://openrouter.ai/api/alpha/decisions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=90) as res:result=json.load(res)
    except urllib.error.HTTPError as exc:
        body=exc.read().decode('utf-8','replace')[:3000]
        raise RuntimeError(f'OpenRouter HTTP {exc.code}: {body}') from None
    if set(result['answers'])!=set(questions):raise ValueError('Incomplete action answers')
    if any(not 0<=x['noul']<=1 for x in result['answers'].values()):raise ValueError('Invalid probabilities')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--questions',default=str(ROOT/'data/questions-v1.json'));p.add_argument('--name',required=True);p.add_argument('--threshold',type=float,default=.75);p.add_argument('--compact',action='store_true');args=p.parse_args()
    if not 0<args.threshold<1:raise SystemExit('Invalid threshold')
    out=ROOT/'runs'/args.name
    if out.exists():raise SystemExit('Use a new run name; never overwrite previous measurements')
    dataset=json.loads(Path(args.dataset).read_text());questions=json.loads(Path(args.questions).read_text())
    key=os.environ.get('OPENROUTER_API_KEY') or getpass.getpass('OpenRouter key (hidden): ')
    if not key:raise SystemExit('No credential')
    out.mkdir(parents=True)
    (out/'manifest.json').write_text(json.dumps({'dataset_sha256':hashlib.sha256(Path(args.dataset).read_bytes()).hexdigest(),'prompt_sha256':hashlib.sha256(Path(args.questions).read_bytes()).hexdigest(),'threshold':args.threshold,'requests_per_transaction':1,'n_planned':len(dataset),'compact_transport':args.compact},indent=2))
    records=[]
    for row in dataset:
        start=time.monotonic()
        response=classify(compact_state(row['state']) if args.compact else row['state'],questions,key) # No expected labels, basis or split in request.
        record={'id':row['id'],'expected':row['expected'],'unassessed':row.get('unassessed',[]),'predicted':[k for k,v in response['answers'].items() if v['noul']>=args.threshold],'response':response,'elapsed_seconds':time.monotonic()-start}
        records.append(record)
        with (out/'results.jsonl').open('a') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(len(records),row['id'][:14],record['predicted'],flush=True)
    result=metrics(records)
    result['usage']={k:sum(r['response'].get('usage',{}).get(k,0) for r in records) for k in ['input_tokens','output_tokens','cost']}
    (out/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print('Macro balanced accuracy:',result['macro_balanced_accuracy'],'classes:',result['evaluated_labels'],'/45',flush=True)
