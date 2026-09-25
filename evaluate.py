"""Macro balanced accuracy; unknown references never become negative examples."""
import json
from taxonomy import build


def metrics(rows):
    labels, _ = build()
    ids = {x['id'] for x in labels}
    report, valid = {}, []
    for r in rows:
        for field in ('expected', 'predicted', 'unassessed'):
            if set(r.get(field, [])) - ids:
                raise ValueError('Unknown label in ' + field)
        if set(r['expected']) & set(r.get('unassessed', [])):
            raise ValueError('A positive reference cannot also be unassessed')
    for label in labels:
        k = label['id']
        tp = fp = tn = fn = skipped = 0
        for r in rows:
            if k in r.get('unassessed', []):
                skipped += 1
                continue
            y, p = k in r['expected'], k in r['predicted']
            tp += y and p
            fp += not y and p
            tn += not y and not p
            fn += y and not p
        positives, negatives = tp + fn, tn + fp
        tpr = tp / positives if positives else None
        tnr = tn / negatives if negatives else None
        score = (tpr + tnr) / 2 if positives and negatives else None
        if score is not None:
            valid.append(score)
        report[k] = {
            'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'positives': positives, 'negatives': negatives, 'unassessed': skipped,
            'balanced_accuracy': score,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tpr, 'specificity': tnr,
            'f1': 2 * tp / (2 * tp + fp + fn) if positives else None,
            'status': 'evaluated' if score is not None else 'unvalidated',
            'unvalidated_reason': None if score is not None else (
                'no_assessed_examples' if not positives and not negatives else
                'no_positive_reference' if not positives else 'no_negative_reference'),
        }
    # Exact-set accuracy requires a fully annotated transaction; unknown labels
    # must not silently be treated as false or used to declare a complete match.
    complete = [r for r in rows if not r.get('unassessed')]
    tp, fp, fn = (sum(x[k] for x in report.values()) for k in ('tp', 'fp', 'fn'))
    return {
        'metric': 'macro_balanced_accuracy',
        'formula': 'mean_over_evaluable_labels((TPR + TNR) / 2)',
        'n': len(rows),
        'macro_balanced_accuracy': sum(valid) / len(valid) if valid else None,
        'evaluated_labels': len(valid), 'total_labels': len(labels),
        'unvalidated_labels': [k for k, v in report.items() if v['status'] == 'unvalidated'],
        'exact_set_accuracy': sum(set(r['expected']) == set(r['predicted']) for r in complete) / len(complete) if complete else None,
        'exact_set_evaluated_transactions': len(complete),
        'micro_precision': tp / (tp + fp) if tp + fp else None,
        'micro_recall': tp / (tp + fn) if tp + fn else None,
        'micro_f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        'per_label': report,
    }

if __name__ == '__main__':
    import sys
    print(json.dumps(metrics(json.load(open(sys.argv[1]))), indent=2))
