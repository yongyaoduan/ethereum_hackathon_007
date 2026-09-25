import json,argparse
from pathlib import Path
from evaluate import metrics
from compact import compact_state
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');args=p.parse_args()
specs=[('final-random-refresh-v1','random-refresh-reference-200-v1.json','random'),('final-coverage-refresh-v1','coverage-final-refresh-v1.json','coverage'),('dev-retired-v7','retired-first-round-development.json','regression')] if args.final else [('dev-diverse-v6','development-diverse-v4.json','development')]
all_rows=[];reports={}
for run,file,split in specs:
 report=json.loads((ROOT/'runs'/run/'metrics.json').read_text());reports[split]=report
 inputs={x['id']:x for x in json.loads((ROOT/'data'/file).read_text())}
 manifest=json.loads((ROOT/'runs'/run/'manifest.json').read_text())
 rows=[json.loads(x) for x in (ROOT/'runs'/run/'results.jsonl').read_text().splitlines()]
 assert len(rows)==manifest['n_planned']
 for row in rows:
  source=inputs[row['id']];row['state']=source['state'];row['model_state']=compact_state(source['state']) if manifest.get('compact_transport') else source['state'];row['basis']=source.get('basis');row['split']=split
 all_rows.extend(rows)
all_rows.sort(key=lambda r:(not bool(r['predicted']),-len(r['predicted']),r['id']))
payload={'run':', '.join(s[0] for s in specs),'phase':'final' if args.final else 'development','taxonomy':json.loads((ROOT/'data/taxonomy.json').read_text()),'metrics':metrics([r for r in all_rows if r['split']!='regression']),'metrics_scope':'Fresh random and coverage only; regression excluded','reports':reports,'transactions':all_rows,'threshold':.75,'inventory':json.loads((ROOT/'data/coverage-inventory.json').read_text()),'limitations':['新的200笔随机集中只有1笔已确认正例（Redeem）；100%不能代表45类总体可靠性。','开发与测试有部分协议实现重叠，不能视为跨协议泛化结果。','部分参考标签证据不足，已逐项标记并排除评分。','首轮随机测试75%，已转为调试材料；新一轮使用未调用过的200笔随机交易及67笔类别样本。回归集不参与独立测试分数。','词表来自 Etherscan；选项解释是本项目的操作定义，不声称复现其私有分类规则。']}
explanations=json.loads((ROOT/'data/explanations-zh.json').read_text())
for label in payload['taxonomy']['labels']:label['explanation_zh']=explanations[label['id']]
(ROOT/'site/dist/data.json').write_text(json.dumps(payload,ensure_ascii=False))
print('Exported',len(all_rows),'real results; phase',payload['phase'])
