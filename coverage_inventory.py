import json,re
from pathlib import Path
from collections import defaultdict
from taxonomy import build
ROOT=Path(__file__).resolve().parent;D=ROOT/'data'
refs={}
for f in ['development-wrapper.json','coverage-reference-draft.json','random-reference-200-v2.json','coverage-final-refresh-v1.json','random-refresh-reference-200-v1.json']:
 for r in json.loads((D/f).read_text()):refs[r['id']]=r
summary={}
paths=list((D/'protocol-discovery').glob('0x*.json'))+list((D/'random').glob('block-*.json'))+list((D/'missing-class-search').glob('*-[0-9]*.json'))
for p in paths:
 for t in json.loads(p.read_text()).get('items',[]):
  if t.get('hash'):summary[t['hash']]=t
patterns={
 'burn':r'^burn', 'cancel_withdrawal':r'cancel.*withdraw|withdraw.*cancel', 'commit':r'^commit',
 'delegate':r'^delegate', 'extend_lock':r'extend.*lock|increase.*unlock|increase.*time',
 'increase_amount':r'increase.*amount|increase.*lock', 'initiate_redemption':r'request.*redeem|request.*redemp|initiate.*redemp',
 'liquidate':r'liquidat', 'migrate':r'migrat', 'renew':r'^renew', 'restake':r'restake',
 'short':r'short|openPosition', 'undelegate':r'undelegate', 'vote':r'^vote|castVote'}
notes={
 'burn':'找到了 MCV2_Bond.burn，但它同时返还储备资产；独立销毁与赎回的边界尚未核定。其他 receipt/跨链内部销毁不能自动作正例。',
 'cancel_withdrawal':'核验到的 batchTogglePendingWithdrawal 是暂停/恢复，未取消申请，不是正例。',
 'commit':'观察到的 CommitStore.transmit 是预言机/消息报告，未确认用户承诺—揭示流程的正例。',
 'delegate':'治理与质押候选中未找到可核验的委托正例。',
 'extend_lock':'已有锁定/解锁案例，但未找到延长既有锁定期限的核验正例。',
 'increase_amount':'普通质押或抵押增加不等于增加既有锁定金额；尚无核验正例。',
 'initiate_redemption':'质押退出与申请提取存在相近案例，独立申请赎回的边界/历史状态不足，未作确定正例。',
 'liquidate':'目录包含 Liquidation 合约，但没有核验到执行清算的交易正例。',
 'migrate':'SafeMigration/SafeToL2Migration/V3Migrator 候选未提供可核验的迁移执行正例。',
 'renew':'找到 HnsRegistrar/HnsController 部署候选，但没有找到可核验续期正例。',
 'restake':'普通质押重复投入不能当再质押；未核验到再质押服务实例。',
 'short':'未核验到明确方向为做空的衍生品交易；普通卖币不是正例。',
 'undelegate':'未找到解除既有治理/验证者委托的核验正例。',
 'vote':'RubyscoreVote.vote 是空 payable 函数，不能作为治理投票正例；Governor 候选仅见部署/角色管理。'}
reports={}
for tag,run in [('fresh_coverage','final-coverage-refresh-v1'),('fresh_random','final-random-refresh-v1'),('regression','dev-retired-v7')]:
 p=ROOT/'runs'/run/'metrics.json'
 if p.exists():reports[tag]=json.loads(p.read_text())
result=[]
for label in build()[0]:
 k=label['id'];pos=[r['id'] for r in refs.values() if k in r['expected']];abi=[]
 if k in patterns:
  for p in (D/'contracts').glob('*.json'):
   c=json.loads(p.read_text())
   for f in c.get('abi') or []:
    if f.get('type')=='function' and re.search(patterns[k],f.get('name',''),re.I):abi.append({'contract':p.stem,'name':c.get('name'),'function':f['name']})
 result.append({'id':k,'label':label['label'],'verified_reference_positives':len(pos),'example_hashes':pos[:6],'status':'reference_examples_found' if pos else 'unvalidated','note':notes.get(k,'有真实参考案例；请区分独立测试、已用于调试的回归样本和小样本限制。'),'abi_search_hits':abi,'scores':{group:r['per_label'][k] for group,r in reports.items()}})
out={'unique_transaction_summaries_examined':len(summary),'verified_contract_catalog_count':len(json.loads((D/'verified-catalog.json').read_text())),'marketplace_history_exhausted':json.loads((D/'missing-class-search/marketplace-summary.json').read_text())['exhausted'],'labels_with_reference_positives':sum(bool(x['verified_reference_positives']) for x in result),'total_labels':45,'scope_limit':'Bounded search, not a claim that unmatched actions never occur anywhere on HSK. Method-filter API timed out; archived registry, protocol histories, full marketplace history and random blocks form the evidence scope.','labels':result}
(D/'coverage-inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('Examined',len(summary),'unique summaries; positive references',out['labels_with_reference_positives'],'/45; unvalidated',[x['label'] for x in result if not x['verified_reference_positives']])
