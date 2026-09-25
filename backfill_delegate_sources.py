"""Archive verified source of actual historical delegate targets."""
import json
from enrich import OUT, contract
seen=set()
for p in sorted(OUT.glob('*.json')):
 d=json.loads(p.read_text());to=(d['transaction'].get('to') or {}).get('hash','').lower()
 for call in d['internal_transactions']:
  a=call.get('to') or {}
  if call.get('type')=='delegatecall' and call.get('success') is True and (call.get('from') or {}).get('hash','').lower()==to and a.get('is_verified') and a['hash'].lower() not in seen:
   seen.add(a['hash'].lower())
   try:
    c=contract(a['hash']);print(a['hash'],c.get('name'),flush=True)
   except Exception as e:print(a['hash'],str(e),flush=True)
