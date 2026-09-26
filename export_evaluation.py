"""Build the current Astra-reference evaluation from the published transaction pool."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from evaluate import metrics

ROOT = Path(__file__).resolve().parent


def export_evaluation():
    source = ROOT / 'data/hackathon-scale/transactions.json'
    manifest = json.loads(source.with_name('manifest.json').read_text())
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != manifest['files']['transactions.json']['sha256']:
        raise ValueError('Evaluation source does not match its manifest')
    pool = json.loads(raw)
    if len(pool) != len({r['id'] for r in pool}) or len(pool) != manifest['transaction_count']:
        raise ValueError('Evaluation transaction count or uniqueness mismatch')
    if dict(Counter(r['classification_status'] for r in pool)) != manifest['classification_status_counts']:
        raise ValueError('Classification status counts differ from the manifest')

    records, failures = [], []
    for row in pool:
        if row['classification_status'] != 'classified':
            if row['predicted'] is not None:
                raise ValueError('Failed classification must retain null predictions')
            failures.append({'id': row['id'], 'reason': row['classification_status']})
            continue
        ref = row['llm_judgment']
        records.append({
            'id': row['id'], 'predicted': row['predicted'],
            'expected': ref['expected'], 'unassessed': ref['unassessed'],
            'basis': ref['basis'], 'cohort': row['cohort'],
            'timestamp': row['state']['transaction']['timestamp'],
        })

    report = metrics(records)
    payload = {
        'schema_version': 1,
        'source': {
            'path': 'data/hackathon-scale/transactions.json', 'sha256': digest,
            'transaction_count': len(pool), 'valid_outputs': len(records),
            'reference': 'Astra', 'human_reviewed': False,
            'cohort_counts': manifest['cohort_counts'],
            'reused_outputs': manifest['reused_successful_outputs'],
            'new_outputs': manifest['new_successful_outputs'],
            'classifier': manifest['classifier'],
        },
        'metrics': report, 'failures': failures, 'transactions': records,
    }
    (ROOT / 'site/dist/evaluation.json').write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')))
    evidence = {r['id']: r['state'] for r in pool if r['classification_status'] == 'classified'}
    (ROOT / 'site/dist/evaluation-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, separators=(',', ':')))
    source.with_name('metrics.json').write_text(json.dumps({'source_sha256': digest, **report}, indent=2) + '\n')
    print(f"Evaluation: {len(records)}/{len(pool)} valid; {report['evaluated_labels']} classes; "
          f"macro BA {report['macro_balanced_accuracy']:.4%}; exact set {report['exact_set_accuracy']:.4%}")
    return payload


if __name__ == '__main__':
    export_evaluation()
