"""Model input comes only from archived on-chain evidence, never gold labels."""
import json
import re
from pathlib import Path
from Crypto.Hash import keccak
ROOT=Path(__file__).resolve().parent

def abi_signature_type(arg):
    typ=arg['type']
    return '('+','.join(abi_signature_type(x) for x in arg['components'])+')'+typ[5:] if typ.startswith('tuple') else typ

def resolve_method(abi, raw_input):
    for item in abi or []:
        if item.get('type')!='function':continue
        signature=item['name']+'('+','.join(abi_signature_type(x) for x in item['inputs'])+')'
        digest=keccak.new(digest_bits=256);digest.update(signature.encode())
        if raw_input[:10].lower()=='0x'+digest.hexdigest()[:8]:return item['name']
    return None

def relevant_source(source,method):
    """Select named function and same-file helper bodies, never execute source."""
    bodies={}
    for match in re.finditer(r'\bfunction\s+(\w+)\s*\(',source):
        start=match.start();brace=source.find('{',start);semi=source.find(';',start)
        if brace<0 or (0<=semi<brace):continue
        depth=1;i=brace+1
        while depth and i<len(source):
            depth+=(source[i]=='{')-(source[i]=='}');i+=1
        bodies.setdefault(match.group(1),[]).append(source[start:i])
    selected=[];pending=[method];seen=set()
    while pending and len(selected)<12:
        name=pending.pop(0)
        if name in seen:continue
        seen.add(name)
        for body in bodies.get(name,[]):
            selected.append(body)
            pending.extend(x for x in re.findall(r'\b(\w+)\s*\(',body) if x in bodies and x not in seen)
    return '\n\n'.join(selected)[:18000]

def state(d):
    t=d['transaction']
    out={'chain_id':177,'transaction':{k:t.get(k) for k in ['hash','block_number','timestamp','status','method','decoded_input','raw_input','value','transaction_types']},'from':(t.get('from') or {}).get('hash'),'to':(t.get('to') or {}).get('hash'),'created_contract':t.get('created_contract'),'pagination_complete':d['pagination_complete']}
    out['logs']=[{'emitter':x['address']['hash'],'decoded':x.get('decoded'),'data':x.get('data'),'topics':x.get('topics')} for x in d['logs']]
    out['internal_calls']=[{'from':(x.get('from') or {}).get('hash'),'to':(x.get('to') or {}).get('hash'),'value':x.get('value'),'type':x.get('type'),'success':x.get('success'),'error':x.get('error'),'created_contract':x.get('created_contract')} for x in d['internal_transactions']]
    out['token_transfers']=[{'from':(x.get('from') or {}).get('hash'),'to':(x.get('to') or {}).get('hash'),'total':x.get('total'),'token':{k:(x.get('token') or {}).get(k) for k in ['address_hash','name','symbol','decimals','type']}} for x in d['token_transfers']]
    out['contracts']=[]
    # Proxy metadata reports today's implementation. Historical delegatecall
    # targets identify the actual implementation used by this transaction.
    direct_to=(t.get('to') or {}).get('hash','').lower()
    executed_targets={
        (x.get('to') or {}).get('hash','').lower()
        for x in d['internal_transactions']
        if x.get('type')=='delegatecall' and x.get('success') is True
        and (x.get('from') or {}).get('hash','').lower()==direct_to
    }
    addresses=[d.get('contract_address')]+sorted(executed_targets)
    for addr in filter(None,addresses):
        path=ROOT/'data/contracts'/f'{addr.lower()}.json'
        if not path.exists():
            out['contracts'].append({'address':addr,'verified':False,'scope':'Executed delegate target; source not archived yet.'})
            continue
        c=json.loads(path.read_text())
        source='\n'.join([c.get('source_code') or '']+[x.get('source_code','') for x in c.get('additional_sources',[])])
        method=t.get('method') or ''
        if method.startswith('0x'):
            resolved=resolve_method(c.get('abi'),t.get('raw_input') or '')
            if resolved:
                method=resolved
                out['transaction']['abi_resolved_method']=resolved
        event_names={(x.get('decoded') or {}).get('method_call','').split('(')[0] for x in d['logs']}
        abi=[x for x in (c.get('abi') or []) if x.get('name')==method or (x.get('type')=='event' and x.get('name') in event_names)]
        excerpt=relevant_source(source,method)
        out['contracts'].append({'address':addr,'name':c.get('name'),'verified':c.get('is_verified'),'relevant_abi':abi,'source_excerpt':excerpt,'scope':'Selected function/helper source is semantic context, NOT evidence that every operation in the source executed. The full original source is archived separately.','implementation_time_scope':'Successful delegatecall target observed in this transaction.' if addr.lower() in executed_targets else 'Direct contract context; current implementation metadata is not used as historical proof.'})
    return out

if __name__=='__main__':
    rows=[]
    for p in sorted((ROOT/'data/evidence').glob('*.json')):
        d=json.loads(p.read_text());t=d['transaction'];to=(t.get('to') or {}).get('hash','').lower()
        if to!='0xb210d2120d57b758ee163cffb43e73728c471cf1' or t.get('method') not in ['deposit','withdraw']:continue
        assert t['status']=='ok' and d['pagination_complete']
        events=[x['decoded']['method_call'].split('(')[0] for x in d['logs'] if x.get('decoded')]
        if t['method']=='deposit':
            assert int(t['value'])>0 and 'Deposit' in events and 'Transfer' in events
            expected=['deposit','wrap']
            basis='Verified WHSK deposit mints exactly msg.value of WHSK for incoming HSK; successful receipt and Deposit + mint Transfer logs. v1 permits Deposit with Wrap and excludes auxiliary Mint.'
        else:
            assert 'Withdrawal' in events and 'Transfer' in events
            assert any(int(x.get('value') or 0)>0 and (x.get('to') or {}).get('hash','').lower()==t['from']['hash'].lower() for x in d['internal_transactions'])
            expected=['withdraw','unwrap']
            basis='Verified WHSK withdraw burns WHSK and sends underlying HSK; successful receipt, Withdrawal + burn Transfer logs and native repayment trace. v1 permits Withdraw with Unwrap and excludes auxiliary Burn.'
        rows.append({'id':t['hash'],'split':'development','expected':expected,'basis':basis,'state':state(d)})
    assert len(rows)==8
    (ROOT/'data/development-wrapper.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print('8 real development examples with explicit source/event reference basis; not held-out accuracy.')
