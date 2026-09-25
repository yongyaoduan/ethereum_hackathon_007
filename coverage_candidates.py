"""Capture diverse real candidates, with zero automatic gold-label assignment."""
import json
from pathlib import Path
from collections import defaultdict
from enrich import enrich
ROOT=Path(__file__).resolve().parent
METHODS=set('addLiquidity addLiquidityETH approve batchMint borrowDebt claim claimDelivery createMarket createPool createSubAccount deploy deposit depositWithPermit exactInputSingle executeExpiredPendingWithdrawal lock mint registerMerchant removeLiquidity repayWithSelectedToken requestUnstakeFlexible requestWithdraw setInterestRateModel stake supplyCollateral supplyLiquidity unlock unstake unstakeLocked vote withdraw withdrawCollateral withdrawLiquidity swapExactETHForTokens swapExactTokensForETH'.split())
if __name__=='__main__':
    planpath=ROOT/'data/coverage-candidate-plan.json'
    if planpath.exists():plan=json.loads(planpath.read_text())
    else:
        grouped=defaultdict(dict)
        for p in sorted((ROOT/'data/protocol-discovery').glob('0x*.json')):
            for t in json.loads(p.read_text())['items']:
                if t.get('method') in METHODS:grouped[t['method']][t['hash']]=t
        selected=[]
        for method,rows in sorted(grouped.items()):
            # Round robin contracts to avoid six nearly identical calls from one deployment.
            contracts=defaultdict(list)
            for t in sorted(rows.values(),key=lambda x:x['hash']):contracts[(t.get('to') or {}).get('hash','')].append(t)
            for i in range(6):
                for c in sorted(contracts):
                    if i<len(contracts[c]):selected.append(contracts[c][i])
                if sum(x['method']==method for x in selected)>=6:break
        # This captures candidates only. Any later test split is frozen before inference.
        plan={'origin':'Real HSK protocol histories; candidate retrieval by methods, NOT reference labels','transactions':selected}
        planpath.write_text(json.dumps(plan,indent=2))
    errors=[]
    for i,t in enumerate(plan['transactions']):
        try:
            d=enrich(t)
            events=[(l.get('decoded') or {}).get('method_call','?').split('(')[0] for l in d['logs']]
            print(i+1,len(plan['transactions']),t['method'],t['hash'][:12],events,flush=True)
        except Exception as e:
            errors.append({'hash':t['hash'],'error':str(e)})
            print(t['hash'],str(e),flush=True)
    (ROOT/'data/coverage-evidence-errors.json').write_text(json.dumps(errors,indent=2))
