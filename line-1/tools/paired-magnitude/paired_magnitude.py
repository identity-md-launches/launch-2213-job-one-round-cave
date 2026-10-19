#!/usr/bin/env python3
"""Deterministic paired bootstrap interval for a continuous benchmark metric."""
import argparse
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

LIMIT = 2 * 1024 * 1024
MAX_CASES = 10000


def finite_mean(values):
    """Mean without overflowing a finite sum whose average is representable."""
    try:
        return math.fsum(values) / len(values)
    except OverflowError:
        scale = max(abs(x) for x in values)
        return (math.fsum(x / scale for x in values) / len(values)) * scale


def percentile(sorted_values, p):
    """Linear interpolation at rank p*(n-1), the usual type-7 quantile."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = p * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    weight = rank - lo
    left, right = sorted_values[lo], sorted_values[hi]
    difference = right - left
    if math.isfinite(difference):
        return left + difference * weight
    return left * (1 - weight) + right * weight


def analyze(deltas, confidence=0.95, replicates=2000, seed=32):
    if not 2 <= len(deltas) <= MAX_CASES:
        raise ValueError("need 2 through 10000 paired cases")
    if not all(type(x) in (int, float) and math.isfinite(x) for x in deltas):
        raise ValueError("all paired differences must be finite")
    if type(confidence) not in (int, float) or not 0.8 <= confidence <= 0.99:
        raise ValueError("confidence must be from 0.80 through 0.99")
    if type(replicates) is not int or not 200 <= replicates <= 20000:
        raise ValueError("replicates must be from 200 through 20000")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    # Fixed SplitMix64 avoids depending on Python's version-specific randrange.
    state = seed & ((1 << 64) - 1)
    mask = (1 << 64) - 1
    threshold = (1 << 64) % len(deltas)

    def randbelow(bound):
        nonlocal state
        while True:
            state = (state + 0x9E3779B97F4A7C15) & mask
            value = state
            value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & mask
            value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & mask
            value ^= value >> 31
            if value >= threshold:
                return value % bound

    n = len(deltas)
    means = [finite_mean([deltas[randbelow(n)] for _ in range(n)]) for _ in range(replicates)]
    means.sort()
    tail = (1 - confidence) / 2
    mean = finite_mean(deltas)
    return {
        "cases": n,
        "mean_difference": mean,
        "median_difference": percentile(sorted(deltas), 0.5),
        "confidence": confidence,
        "percentile_interval": [percentile(means, tail), percentile(means, 1 - tail)],
        "bootstrap_replicates": replicates,
        "seed": seed,
        "random_generator": "SplitMix64-v1",
        "method": "case-level paired percentile bootstrap; linear type-7 quantiles",
        "direction": "candidate higher" if mean > 0 else "candidate lower" if mean < 0 else "equal sample means",
    }


def read_csv(path):
    root = Path.cwd().resolve()
    candidate = Path(path).resolve(strict=True)
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError("input must be a regular file inside the current workspace")
    with candidate.open("rb") as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError("CSV exceeds 2 MiB")
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if reader.fieldnames != ["case", "baseline", "candidate"]:
            raise ValueError("header must be exactly: case,baseline,candidate")
        ids, deltas = set(), []
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f"line {line}: expected exactly three fields")
            name = row["case"]
            if not name or name != name.strip() or name in ids or any(ord(c) < 32 or ord(c) == 127 for c in name):
                raise ValueError(f"line {line}: case ID must be unique and have no edge whitespace")
            ids.add(name)
            baseline, candidate_value = float(row["baseline"]), float(row["candidate"])
            if not math.isfinite(baseline) or not math.isfinite(candidate_value):
                raise ValueError(f"line {line}: metrics must be finite numbers")
            difference = candidate_value - baseline
            if not math.isfinite(difference):
                raise ValueError(f"line {line}: paired difference exceeds finite float range")
            deltas.append(difference)
            if len(deltas) > MAX_CASES:
                raise ValueError("CSV exceeds 10000 paired cases")
        return deltas, hashlib.sha256(raw).hexdigest()
    except (UnicodeDecodeError, csv.Error, OverflowError) as exc:
        raise ValueError(f"invalid UTF-8 CSV: {exc}") from exc


def demo():
    # Synthetic paired latency improvements (candidate minus baseline, ms).
    return [-18, -11, -9, -8, -7, -6, -4, -3, -2, 1, 2, 5]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="paired CSV: case,baseline,candidate")
    source.add_argument("--demo", action="store_true", help="run the explicitly synthetic example")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=32)
    args = parser.parse_args()
    try:
        if args.demo:
            deltas, digest = demo(), None
        else:
            deltas, digest = read_csv(args.input)
        result = analyze(deltas, args.confidence, args.replicates, args.seed)
        result["input_sha256"] = digest
        if args.demo:
            result["fixture"] = "synthetic illustration, not measured system performance"
        print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False))
    except (OSError, ValueError, csv.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
