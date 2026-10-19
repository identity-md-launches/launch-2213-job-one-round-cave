#!/usr/bin/env python3
"""Exact paired continuous-metric sign-flip evidence for a declared family."""
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sys
import unicodedata

LIMIT = 2 * 1024 * 1024
SCALE = 10**6
MAX_CASES = 200
MAX_CANDIDATES = 16
MAX_WEIGHT = 20000
MAX_WORK = 2000000
DECIMAL = re.compile(r'[+-]?(?:0|[1-9][0-9]{0,9})(?:\.[0-9]{1,6})?\Z')
PIN = re.compile(r'[0-9a-f]{64}\Z')


def fraction_json(value):
    return {'numerator': value.numerator, 'denominator': value.denominator}


def label(value):
    if (not value or len(value) > 200 or value != value.strip()
            or any(unicodedata.category(c).startswith('C') for c in value)):
        raise ValueError('labels need 1-200 characters, no controls or edge whitespace')
    return value


def metric(value):
    """Parse the declared decimal grammar into exact millionths, never floats."""
    if not isinstance(value, str) or not DECIMAL.fullmatch(value):
        raise ValueError('metrics need plain decimal notation with at most six decimal places')
    result = Fraction(value) * SCALE
    if abs(result) > 10**9 * SCALE:
        raise ValueError('metric magnitude exceeds 1000000000')
    return result.numerator


def parse_csv(raw):
    if not isinstance(raw, bytes) or len(raw) > LIMIT:
        raise ValueError('input must be bytes, at most 2 MiB')
    try:
        rows = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        header = next(rows, [])
        if (not 3 <= len(header) <= 2 + MAX_CANDIDATES
                or header[:2] != ['case', 'baseline']):
            raise ValueError('header must be case,baseline followed by 1-16 candidate names')
        for name in header:
            label(name)
        if len(set(header)) != len(header):
            raise ValueError('header names must be distinct')
        names, ids = header[2:], set()
        vectors = [[] for _ in names]
        for row in rows:
            if len(ids) >= MAX_CASES:
                raise ValueError('at most 200 paired cases are supported')
            if len(row) != len(header):
                raise ValueError('each row must contain exactly the declared fields; no blank rows')
            case = label(row[0])
            if case in ids:
                raise ValueError('case IDs must be unique')
            ids.add(case)
            base = metric(row[1])
            for values, cell in zip(vectors, row[2:]):
                values.append(metric(cell) - base)
        if len(ids) < 2:
            raise ValueError('at least two paired cases are required')
        return names, vectors
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError('invalid UTF-8 CSV') from exc


def sign_flip(differences):
    """Count all sign assignments via the exact subset-sum polynomial."""
    if (not 2 <= len(differences) <= MAX_CASES
            or any(type(x) is not int or abs(x) > 2 * 10**9 * SCALE for x in differences)):
        raise ValueError('differences must be 2-200 bounded integer millionths')
    divisor = 0
    for value in differences:
        divisor = math.gcd(divisor, abs(value))
    divisor = divisor or 1
    signed = [x // divisor for x in differences]
    weights = sorted(abs(x) for x in signed if x)
    total = sum(weights)
    # Bound dense allocation and arithmetic before starting computation.
    if total > MAX_WEIGHT or len(weights) * (total + 1) > MAX_WORK:
        raise ValueError('exact sign-flip budget exceeded; no rounding or sampled fallback is used')
    counts = [1]
    for weight in weights:
        old_length = len(counts)
        counts.extend([0] * weight)
        for s in range(old_length - 1, -1, -1):
            counts[s + weight] += counts[s]
    assignments = 1 << len(weights)
    if sum(counts) != assignments:
        raise ValueError('internal sign-count conservation failure')
    observed = abs(sum(signed))
    extreme = sum(count for subset, count in enumerate(counts)
                  if abs(total - 2 * subset) >= observed)
    return Fraction(extreme, assignments), {
        'nonzero_pairs': len(weights),
        'zero_pairs': len(differences) - len(weights),
        'gcd_in_millionths': divisor,
        'reduced_absolute_sum': total,
        'extreme_assignments': extreme,
        'sign_assignments': assignments,
    }


def holm(pvalues):
    """Exact Holm adjusted p-values, returned in original family order."""
    adjusted = [Fraction(1)] * len(pvalues)
    maximum = Fraction(0)
    for rank, index in enumerate(sorted(range(len(pvalues)), key=lambda i: (pvalues[i], i))):
        maximum = max(maximum, min(Fraction(1), pvalues[index] * (len(pvalues) - rank)))
        adjusted[index] = maximum
    return adjusted


def alpha_value(value):
    # Deliberately share the plain-decimal grammar with observed values.
    parsed = Fraction(metric(value), SCALE)
    if not Fraction(1, 10**6) <= parsed <= Fraction(1, 5):
        raise ValueError('alpha must be from 0.000001 through 0.2')
    return parsed


def analyze(raw, alpha='0.05', better='lower'):
    if better not in ('lower', 'higher'):
        raise ValueError('better must be lower or higher')
    threshold = alpha_value(alpha)
    names, vectors = parse_csv(raw)
    tests = [sign_flip(vector) for vector in vectors]
    adjusted = holm([test[0] for test in tests])
    reports = []
    for name, values, (pvalue, diagnostics), corrected in zip(names, vectors, tests, adjusted):
        effect = Fraction(sum(values), SCALE * len(values))
        favorable = (effect < 0 if better == 'lower' else effect > 0)
        direction = 'tie' if not effect else 'candidate ahead' if favorable else 'baseline ahead'
        reports.append({
            'candidate': name,
            'mean_candidate_minus_baseline': fraction_json(effect),
            'direction': direction,
            'raw_p': fraction_json(pvalue),
            'holm_p': fraction_json(corrected),
            'reject': corrected <= threshold,
            'reject_with_candidate_ahead': corrected <= threshold and favorable,
            'counting': diagnostics,
        })
    return {
        'schema': 'metric-verdict-v1',
        'input_sha256': hashlib.sha256(raw).hexdigest(),
        'cases': len(vectors[0]),
        'family': names,
        'alpha': fraction_json(threshold),
        'better': better,
        'method': 'exact two-sided paired sign flips of the sum; inclusive tails; Holm family correction',
        'assumptions': [
            'Under each tested null, nonzero paired differences have independent fair signs conditional on their magnitudes.',
            'A justified independent within-pair randomized swap under a sharp null, or a sign-symmetric independent difference model, can supply this assumption.',
            'Independent cases or zero mean alone do not supply sign symmetry; correlated pairs require another model.',
            'Fix metric, units, case set, pass/measurement procedure, candidate family, alpha and analysis before seeing outcomes.',
        ],
        'limitations': [
            'No population generalization, practical-value threshold, confidence interval or adaptive-stopping guarantee is supplied.',
            'A digest binds bytes, not measurement truth, authorship or preregistration time.',
            'Two-sided rejection can favor the baseline; non-rejection does not establish equivalence.',
        ],
        'candidates': reports,
    }


def read_input(path, pin):
    if not isinstance(pin, str) or not PIN.fullmatch(pin):
        raise ValueError('expected SHA-256 must be 64 lowercase hexadecimal digits')
    root = Path.cwd().resolve()
    target = Path(path).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError('input must resolve to a regular file inside the current workspace')
    with target.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('CSV exceeds 2 MiB')
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError('input SHA-256 does not match independently retained pin')
    return raw


def demo():
    # Authored, hypothetical latency measurements; not real benchmark evidence.
    return ('case,baseline,small_step,large_step\n' + ''.join(
        f'case-{i},10.000,9.875,9.500\n' for i in range(1, 9))).encode('ascii')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input')
    source.add_argument('--demo', action='store_true')
    parser.add_argument('--expected-input-sha256')
    parser.add_argument('--alpha', default='0.05')
    parser.add_argument('--better', choices=('lower', 'higher'), default='lower')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if args.expected_input_sha256 is not None:
                raise ValueError('a pin belongs with --input, not --demo')
            raw = demo()
        else:
            raw = read_input(args.input, args.expected_input_sha256)
        result = analyze(raw, args.alpha, args.better)
        if args.demo:
            result['fixture'] = 'synthetic latency illustration, not measured system performance'
        print(json.dumps(result, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':')))
        return 0
    except (OSError, ValueError) as exc:
        # Errors contain only controlled messages or OS path errors, ASCII escaped.
        print('error: ' + ascii(str(exc)), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
