"""Offline regressions; all transient fixtures live under /tmp."""
import contextlib
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().with_name('paired_magnitude.py')
spec = importlib.util.spec_from_file_location('paired_magnitude', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MagnitudeTests(unittest.TestCase):
    def test_demo_golden_and_repeatability(self):
        a = m.analyze(m.demo())
        self.assertEqual(a, m.analyze(m.demo()))
        self.assertEqual(a['mean_difference'], -5)
        self.assertEqual(a['median_difference'], -5)
        self.assertAlmostEqual(a['percentile_interval'][0], -8.41875)
        self.assertEqual(a['percentile_interval'][1], -1.5)
        self.assertNotEqual(a, m.analyze(m.demo(), seed=33))

    def test_constant_and_direction(self):
        for value, direction in [(4, 'candidate higher'), (-4, 'candidate lower'), (0, 'equal sample means')]:
            result = m.analyze([value] * 3, replicates=200)
            self.assertEqual(result['percentile_interval'], [value, value])
            self.assertEqual(result['direction'], direction)

    def test_quantiles_independent_weighted_reference(self):
        for values in itertools.combinations_with_replacement([-5., 0., 2., 9.], 4):
            for p in [0, .025, .1, .5, .975, 1]:
                rank = p * 3
                lo, hi = math.floor(rank), math.ceil(rank)
                expected = values[lo] * (1 - (rank-lo)) + values[hi] * (rank-lo)
                self.assertAlmostEqual(m.percentile(values, p), expected)
        self.assertEqual(m.percentile([7], .5), 7)

    def test_splitmix_stream_against_independent_bootstrap(self):
        # A separate explicit stream and materialized index vectors, not the
        # production closure or averaging/quantile helper.
        state, mask = 32, 2**64-1
        values = [-3, 0, 7]
        means = []
        for _ in range(200):
            sample = []
            while len(sample) < 3:
                state = (state + 0x9e3779b97f4a7c15) % 2**64
                z = state
                z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & mask
                z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & mask
                z = z ^ (z >> 31)
                if z >= 2**64 % 3:
                    sample.append(values[z % 3])
            means.append(sum(sample) / 3)
        means.sort()
        actual = m.analyze(values, confidence=.8, replicates=200)['percentile_interval']
        for p, endpoint in zip([.1, .9], actual):
            rank = p * 199
            lo = math.floor(rank)
            expected = means[lo] * (1-rank+lo) + means[lo+1] * (rank-lo)
            self.assertAlmostEqual(endpoint, expected)

    def test_extreme_finite_values_stay_finite(self):
        for values in ([1e308, 1e308], [-1e308, -1e308], [-1e308, 1e308], [1e308, 1, -1e308]):
            result = m.analyze(values, replicates=200)
            json.dumps(result, allow_nan=False)
            for value in result['percentile_interval']:
                self.assertTrue(min(values) <= value <= max(values))
        self.assertEqual(m.analyze([1e308, 1e308], replicates=200)['median_difference'], 1e308)
        self.assertEqual(m.percentile([-1e308, 1e308], .5), 0)

    def test_invalid_analysis_options(self):
        for values in ([], [1], [float('nan'), 1], [float('inf'), 1], [True, 1], ['1', 2]):
            with self.assertRaises(ValueError):
                m.analyze(values)
        for options in ({'confidence': .79}, {'confidence': float('nan')}, {'confidence': '0.95'}, {'replicates': 199}, {'replicates': 20001}, {'replicates': 200.0}, {'seed': 1.2}, {'seed': True}):
            with self.assertRaises(ValueError):
                m.analyze([1, 2], **options)

    @contextlib.contextmanager
    def workspace(self):
        before = Path.cwd()
        with tempfile.TemporaryDirectory(prefix='paired-magnitude-') as folder:
            try:
                os.chdir(folder)
                yield Path(folder)
            finally:
                os.chdir(before)

    def test_csv_digest_unicode_bom_crlf_and_immutability(self):
        with self.workspace():
            raw = '\ufeffcase,baseline,candidate\r\n"a,猫",10,7\r\nb,2,4\r\n'.encode()
            Path('data.csv').write_bytes(raw)
            values, digest = m.read_csv('data.csv')
            self.assertEqual(values, [-3, 2])
            self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
            self.assertEqual(Path('data.csv').read_bytes(), raw)

    def test_csv_invalid_records(self):
        bodies = ['bad,baseline,candidate\na,1,2\nb,3,4\n',
                  'case,baseline,candidate\na,1,2\na,3,4\n',
                  'case,baseline,candidate\n a,1,2\nb,3,4\n',
                  'case,baseline,candidate\n"a\nb",1,2\nc,3,4\n',
                  'case,baseline,candidate\na,1\nb,3,4\n',
                  'case,baseline,candidate\na,1,2,3\nb,3,4\n',
                  'case,baseline,candidate\na,NaN,2\nb,3,4\n',
                  'case,baseline,candidate\na,-1e308,1e308\nb,3,4\n',
                  'case,baseline,candidate\n"a,1,2\nb,3,4\n']
        with self.workspace():
            for body in bodies:
                Path('data.csv').write_text(body)
                with self.subTest(body=body), self.assertRaises(ValueError):
                    m.read_csv('data.csv')
            Path('data.csv').write_bytes(b'\xff')
            with self.assertRaises(ValueError):
                m.read_csv('data.csv')

    def test_size_case_limit_and_escape(self):
        with self.workspace() as folder:
            Path('data.csv').write_bytes(b'x' * (m.LIMIT + 1))
            with self.assertRaises(ValueError):
                m.read_csv('data.csv')
            Path('data.csv').write_text('case,baseline,candidate\n' + ''.join(f'{i},0,1\n' for i in range(m.MAX_CASES+1)))
            with self.assertRaises(ValueError):
                m.read_csv('data.csv')
            Path('child').mkdir()
            Path('child/link').symlink_to(folder / 'data.csv')
            os.chdir('child')
            with self.assertRaises(ValueError):
                m.read_csv('link')

    def test_standalone_cli_success_and_clean_failure(self):
        with self.workspace():
            shutil.copyfile(SOURCE, 'paired_magnitude.py')
            cli = [sys.executable, '-B', 'paired_magnitude.py']
            result = subprocess.run(cli + ['--demo', '--replicates', '200'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('synthetic', json.loads(result.stdout)['fixture'])
            Path('extreme.csv').write_text('case,baseline,candidate\na,0,1e308\nb,0,1e308\n')
            result = subprocess.run(cli + ['--input', 'extreme.csv', '--replicates', '200'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['percentile_interval'], [1e308, 1e308])
            for args in (['--input', 'missing.csv'], ['--demo', '--confidence', 'nan'], ['--demo', '--replicates', '0']):
                result = subprocess.run(cli + args, capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
