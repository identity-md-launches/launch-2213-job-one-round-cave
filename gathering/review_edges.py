#!/usr/bin/env python3
"""Reproduce bounded inherited coverage gaps without modifying any line."""
import importlib.util
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent.parent


def load(name, source):
    spec = importlib.util.spec_from_file_location(name, ROOT/source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    norm = load('edge_norm', 'line-2/tools/unicode-normalization/unicode_normalization.py')
    percent = load('edge_percent', 'line-2/tools/percent-unicode/percent_unicode.py')
    lens = load('edge_lens', 'line-3/tools/uncertainty-lens/uncertainty_lens.py')
    text = '\u1100\u1161'
    report = norm.review(text.encode())
    try:
        percent.scan(b'%-1')
        percent_error = None
    except ValueError as exc:
        percent_error = str(exc)
    events = [{'id': 'a', 'start': float('nan'), 'end': 1},
              {'id': 'b', 'start': 2, 'end': 3}]
    lens_result = lens.analyze(events)
    result = {
        'normalization_hangul': {'input_escaped': text.encode('unicode_escape').decode(),
            'whole_string_nfc_escaped': unicodedata.normalize('NFC', text).encode('unicode_escape').decode(),
            'inherited_finding_count': report['finding_count'],
            'issue': 'Whole-string normalization changes but inherited sequence scanner reports zero.'},
        'percent_malformed': {'input': '%-1', 'exception': percent_error,
            'issue': 'Malformed percent escape causes uncaught bytearray ValueError in upstream CLI.'},
        'uncertainty_lens_nonfinite': {'accepted_nonfinite_start': True, 'observed': lens_result,
            'issue': 'Nonfinite endpoints are accepted and participate in pairwise order analysis.'},
        'line_files_changed': False,
        'limits': 'Tiny constructed regression probes, not observed attacks or real incident evidence.'}
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))


if __name__ == '__main__':
    main()
