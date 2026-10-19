#!/usr/bin/env python3
"""Retain exact metric evidence while reviewing normalization of its labels."""
import argparse
import csv
import hashlib
import io
import json
import sys
import unicodedata

from engines import metric_verdict as metric
from engines import unicode_normalization as normalization


def review(raw, pin, alpha='0.05', better='lower', max_details=20):
    if not isinstance(pin, str) or not metric.PIN.fullmatch(pin):
        raise ValueError('require an independently retained lowercase SHA-256')
    if not isinstance(raw, bytes) or hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('CSV digest mismatch')
    if type(max_details) is not int or not 0 <= max_details <= 1000:
        raise ValueError('max_details must be an integer from 0 to 1000')
    # Full-family validation and inference use unchanged bytes and labels.
    evidence = metric.analyze(raw, alpha, better)
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True))
    labels = [('header', 1, col + 1, value) for col, value in enumerate(rows[0])]
    labels += [('case', row + 2, 1, cells[0]) for row, cells in enumerate(rows[1:])]
    changes, collisions = [], []
    groups = {}
    for scope, row, col, value in labels:
        forms = {form: unicodedata.normalize(form, value) for form in ('NFC', 'NFKC')}
        ref = {'scope': scope, 'csv_record': row, 'csv_column': col, 'original': value,
               'label_utf8_sha256': hashlib.sha256(value.encode()).hexdigest()}
        if any(result != value for result in forms.values()):
            # The inherited span review is label-relative, not a raw CSV citation.
            spans = normalization.review(value.encode(), 0)
            changes.append({**ref, 'normalized': forms,
                            'inherited_sequence_finding_count': spans['finding_count']})
        for form, result in forms.items():
            groups.setdefault((scope, form, result), []).append(ref)
    for (scope, form, result), members in groups.items():
        if len(members) > 1:
            collisions.append({'scope': scope, 'form': form, 'normalized': result,
                               'members': members})
    return {'schema': 'metric-label-review/1', 'evidence': evidence,
            'unicode_version': unicodedata.unidata_version,
            'labels_checked': len(labels), 'normalization_changed_labels': len(changes),
            'collision_groups': len(collisions),
            'review_required': bool(changes or collisions),
            'changed_labels': changes[:max_details],
            'collision_details': collisions[:max_details],
            'omitted_changed_labels': max(0, len(changes) - max_details),
            'omitted_collision_groups': max(0, len(collisions) - max_details),
            'limitations': [
                'Whole-label NFC/NFKC comparison supplements the inherited per-sequence scanner, including Hangul composition.',
                'CSV coordinates are logical records and columns, not physical lines or raw-byte offsets.',
                'Label digests bind decoded UTF-8 labels; the evidence digest separately binds original CSV bytes.',
                'No label is rewritten, merged or dropped; evidence retains the entire declared family.',
                'Normalization can be legitimate. No confusable-font, rendering, safety or authenticity verdict is supplied.',
                'Pins bind bytes, not truth or preregistration; all sign-flip assumptions in the evidence apply.',
                'Details are capped separately for changed labels and collision groups; complete counts remain.',
            ]}


def demo_bytes():
    return ('case,baseline,model-A,model-\uff21\n'
            + ''.join(f'{name},10,9,8\n' for name in ['caf\u00e9', 'cafe\u0301', '\uac00', '\u1100\u1161'])).encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('demo', 'review'))
    parser.add_argument('--expected-input-sha256')
    parser.add_argument('--max-details', type=int, default=20)
    parser.add_argument('--alpha', default='0.05')
    parser.add_argument('--better', choices=('lower', 'higher'), default='lower')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'demo':
            if args.expected_input_sha256 is not None:
                raise ValueError('demo uses its own synthetic bytes')
            raw = demo_bytes()
            pin = hashlib.sha256(raw).hexdigest()
        else:
            raw = sys.stdin.buffer.read(metric.LIMIT + 1)
            if len(raw) > metric.LIMIT:
                raise ValueError('CSV exceeds 2 MiB')
            pin = args.expected_input_sha256
        result = review(raw, pin, args.alpha, args.better, args.max_details)
        if args.mode == 'demo':
            result['fixture'] = 'synthetic labels and measurements; no real performance claim'
        print(json.dumps(result, ensure_ascii=True, allow_nan=False, sort_keys=True))
        return 0
    except (ValueError, OSError) as exc:
        print('error: ' + ascii(str(exc)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
