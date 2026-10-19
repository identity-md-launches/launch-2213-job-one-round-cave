import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import metric_label_review as app


def check(raw, **kwargs):
    return app.review(raw, hashlib.sha256(raw).hexdigest(), **kwargs)


class LabelReviewTests(unittest.TestCase):
    def test_demo_collisions_include_hangul_and_candidate_family(self):
        result = check(app.demo_bytes())
        self.assertEqual(result['normalization_changed_labels'], 3)
        self.assertEqual(result['collision_groups'], 5)
        self.assertEqual(result['labels_checked'], 8)
        self.assertEqual(result['evidence']['family'], ['model-A', 'model-\uff21'])
        self.assertTrue(any(c['normalized'] == '\uac00' for c in result['collision_details']))

    def test_inference_is_exactly_unchanged(self):
        raw = app.demo_bytes()
        for better in ('lower', 'higher'):
            self.assertEqual(check(raw, better=better)['evidence'], app.metric.analyze(raw, better=better))

    def test_no_findings_is_not_rejection(self):
        result = check(app.metric.demo())
        self.assertFalse(result['review_required'])
        self.assertEqual(result['evidence']['cases'], 8)

    def test_detail_caps_preserve_counts_and_evidence(self):
        full = check(app.demo_bytes())
        capped = check(app.demo_bytes(), max_details=0)
        self.assertEqual(capped['collision_details'], [])
        self.assertEqual(capped['changed_labels'], [])
        self.assertEqual(capped['omitted_collision_groups'], 5)
        self.assertEqual(capped['omitted_changed_labels'], 3)
        self.assertEqual(capped['evidence'], full['evidence'])

    def test_scopes_do_not_merge_and_decoded_label_hashes(self):
        raw = '\ufeffcase,baseline,"a,b"\r\n"a,b",1,2\r\nx,3,4\r\n'.encode()
        result = check(raw)
        self.assertEqual(result['collision_groups'], 0)
        self.assertEqual(result['evidence']['input_sha256'], hashlib.sha256(raw).hexdigest())
        result = check(app.demo_bytes())
        for detail in result['changed_labels']:
            self.assertEqual(detail['label_utf8_sha256'], hashlib.sha256(detail['original'].encode()).hexdigest())

    def test_invalid_pin_and_options(self):
        raw = app.demo_bytes()
        for pin in (None, '', 'A'*64, hashlib.sha256(raw+b'x').hexdigest()):
            with self.assertRaises(ValueError):
                app.review(raw, pin)
        for cap in (-1, 1001, True, 1.5):
            with self.assertRaises(ValueError):
                check(raw, max_details=cap)

    def test_invalid_csv_never_produces_partial_family(self):
        for raw in (b'case,baseline,a,a\nx,1,2,3\ny,1,2,3\n',
                    b'case,baseline,a\nx,1,2\nx,3,4\n', b'\xff',
                    b'case,baseline,a\nx,1,NaN\ny,1,2\n'):
            with self.assertRaises(ValueError):
                check(raw)

    def test_snapshot_provenance(self):
        here = Path(__file__).resolve().parent
        for row in json.loads((here/'provenance.json').read_text()):
            self.assertEqual(hashlib.sha256((here/row['copy']).read_bytes()).hexdigest(), row['sha256'])

    def test_standalone_cli_ascii_success_and_clean_errors(self):
        scratch = Path('test/scratch').resolve()
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            target = Path(directory)/'tool'
            shutil.copytree(Path(__file__).resolve().parent, target)
            cmd = [sys.executable, '-B', str(target/'metric_label_review.py')]
            good = subprocess.run(cmd+['demo'], cwd=target, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            good.stdout.decode('ascii')
            self.assertTrue(json.loads(good.stdout)['review_required'])
            raw = app.demo_bytes()
            result = subprocess.run(cmd+['review', '--expected-input-sha256', hashlib.sha256(raw).hexdigest()],
                                    cwd=target, input=raw, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            bad = subprocess.run(cmd+['review'], cwd=target, input=raw, capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')
            self.assertNotIn(b'Traceback', bad.stderr)


if __name__ == '__main__':
    unittest.main()
