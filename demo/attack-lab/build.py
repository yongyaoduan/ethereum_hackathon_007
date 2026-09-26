"""Embed the authored cases in the standalone page; standard library only."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
template = (root / 'index.template.html').read_text()
assert template.count('__ATTACK_DEMO_DATA__') == 1
data = json.loads((root / 'cases.json').read_text())
embedded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
(root / 'index.html').write_text(template.replace('__ATTACK_DEMO_DATA__', embedded))
print('Built standalone index.html with 6 synthetic specimens.')
