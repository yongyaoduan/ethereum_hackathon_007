"""Deterministic transport encoding: deduplicate public addresses/ABI event shapes.
Original complete evidence remains in the frozen dataset. No labels enter here.
"""
import copy,re

def compact_state(original):
 s=copy.deepcopy(original);addresses={};templates={}
 def replace(value):
  if isinstance(value,str) and re.fullmatch(r'0x[0-9a-fA-F]{40}',value):
   lower=value.lower()
   if lower not in addresses:addresses[lower]='A'+str(len(addresses))
   return addresses[lower]
  if isinstance(value,list):return [replace(x) for x in value]
  if isinstance(value,dict):return {k:replace(v) for k,v in value.items() if v is not None}
  return value
 # A decoded call is the interpretable ABI rendering of raw calldata. Keep raw
 # calldata for undecoded calls, never discard opaque evidence wholesale.
 if s['transaction'].get('decoded_input'):s['transaction'].pop('raw_input',None)
 logs=[]
 for log in s.pop('logs',[]):
  decoded=log.get('decoded')
  if not decoded:logs.append({'raw':replace(log)});continue
  shape=(decoded.get('method_call',''),tuple((p.get('name'),p.get('type'),p.get('indexed')) for p in decoded.get('parameters',[])))
  if shape not in templates:templates[shape]='E'+str(len(templates))
  logs.append([replace(log['emitter']),templates[shape],[replace(p.get('value')) for p in decoded.get('parameters',[])]])
 s['event_templates']={v:{'signature':k[0],'parameters':[{'name':x[0],'type':x[1],'indexed':x[2]} for x in k[1]]} for k,v in templates.items()}
 s['logs']={'columns':['emitter_address_alias','event_template','parameter_values_in_order'],'rows':logs}
 transfers=[];tokens={}
 for t in s.pop('token_transfers',[]):
  token=t['token'];key=token.get('address_hash') or repr(token)
  if key not in tokens:tokens[key]=(f'T{len(tokens)}',replace(token))
  transfers.append([replace(t.get('from')),replace(t.get('to')),tokens[key][0],replace({k:v for k,v in (t.get('total') or {}).items() if k!='token_instance'})])
 s['tokens']={v[0]:v[1] for v in tokens.values()}
 s['token_transfers']={'columns':['from_address_alias','to_address_alias','token_id_in_tokens','amount_or_nft_id'],'rows':transfers}
 s=replace(s)
 s['address_aliases']={v:k for k,v in addresses.items()}
 s['encoding_note']='Lossless address aliases and event templates; log order preserved. Decoded logs/call replace duplicate raw bytes, while undecoded raw evidence is retained. NFT media metadata is excluded; token IDs and quantities are retained. Full original input is archived.'
 return s
