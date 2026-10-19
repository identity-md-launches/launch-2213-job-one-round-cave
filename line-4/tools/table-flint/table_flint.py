#!/usr/bin/env python3
"""Check sums and means of a CSV table with exact dimensional arithmetic."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
import sys

import engine

MAX_BYTES = 262144
MAX_ROWS = 4096
MAX_COLUMNS = 16


class TableError(ValueError):
    pass


def quantity(source: str, where: str) -> engine.Quantity:
    if not source.strip():
        raise TableError(f"{where}: empty quantity")
    try:
        return engine.Parser(source).parse()
    except engine.UnitError as exc:
        raise TableError(f"{where}: {exc} at character {exc.pos}") from exc


def bounded(value: Fraction, dims: engine.Dimensions) -> Fraction:
    try:
        engine.Parser.bounded(engine.Quantity(value, dims), 0)
    except engine.UnitError as exc:
        raise TableError(str(exc)) from exc
    return value


def compute(data: bytes, value_column: str = "value", weight_column: str | None = None,
            to: str | None = None, claims: dict[str, str] | None = None) -> dict:
    if len(data) > MAX_BYTES:
        raise TableError(f"CSV exceeds {MAX_BYTES} bytes")
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TableError("CSV must be UTF-8") from exc
    try:
        reader = csv.reader(io.StringIO(source, newline=""), strict=True)
        header = next(reader, None)
        if header is None or not 1 <= len(header) <= MAX_COLUMNS:
            raise TableError("CSV needs a header with 1..16 columns")
        if any(not field or field != field.strip() for field in header) or len(set(header)) != len(header):
            raise TableError("CSV header has an empty, padded or duplicate column name")
        if value_column not in header:
            raise TableError(f"missing value column {value_column!r}")
        if weight_column is not None and (weight_column not in header or weight_column == value_column):
            raise TableError("weight column must be distinct and present")
        vi = header.index(value_column)
        wi = header.index(weight_column) if weight_column is not None else None
        count, total, weighted_total, weight_total = 0, Fraction(), Fraction(), Fraction()
        smallest = largest = None
        dims = None
        for row in reader:
            count += 1
            if count > MAX_ROWS:
                raise TableError(f"CSV exceeds {MAX_ROWS} data rows")
            if len(row) != len(header):
                raise TableError(f"row {count}: expected {len(header)} columns, got {len(row)}")
            q = quantity(row[vi], f"row {count} value")
            if dims is None:
                dims = q.dims
            elif q.dims != dims:
                raise TableError(f"row {count}: dimension {engine.dimensions(q.dims)} differs from {engine.dimensions(dims)}")
            total = bounded(total + q.value, dims)
            smallest = q.value if smallest is None else min(smallest, q.value)
            largest = q.value if largest is None else max(largest, q.value)
            if wi is not None:
                weight = quantity(row[wi], f"row {count} weight")
                if weight.dims != engine.ZERO or weight.value < 0:
                    raise TableError(f"row {count}: weight must be nonnegative and dimensionless")
                weight_total = bounded(weight_total + weight.value, engine.ZERO)
                weighted_total = bounded(weighted_total + weight.value * q.value, dims)
        if count == 0:
            raise TableError("CSV needs at least one data row")
        if wi is not None and weight_total == 0:
            raise TableError("total weight must be positive")
    except csv.Error as exc:
        raise TableError(f"malformed CSV: {exc}") from exc
    mean = bounded(total / count, dims)
    results = {"sum": total, "mean": mean, "minimum": smallest, "maximum": largest}
    if wi is not None:
        results["weighted_mean"] = bounded(weighted_total / weight_total, dims)
    if to is None:
        scale, label = Fraction(1), engine.dimensions(dims)
    else:
        target = quantity(to, "target unit")
        if target.value <= 0 or target.dims != dims:
            raise TableError("target unit must have positive scale and matching dimensions")
        scale, label = target.value, to
    for name, value in results.items():
        bounded(value / scale, dims)
    checks = {}
    for name, expression in (claims or {}).items():
        if name not in ("sum", "mean", "weighted_mean") or name not in results:
            raise TableError(f"claim {name!r} does not name an available result")
        expected = quantity(expression, f"{name} claim")
        if expected.dims != dims:
            raise TableError(f"{name} claim has incompatible dimensions")
        checks[name] = {"claim": expression, "expected_base_value": engine.exact_decimal(expected.value),
                        "difference_base_value": engine.exact_decimal(results[name] - expected.value),
                        "matches": results[name] == expected.value}
    return {"schema": "table-flint/1", "csv_sha256": hashlib.sha256(data).hexdigest(),
            "rows": count, "value_column": value_column, "weight_column": weight_column,
            "unit": label, "base_unit": engine.dimensions(dims),
            "dimensions": dict(zip(("length", "mass", "time", "data"), dims)),
            "values": {name: {"value": engine.exact_decimal(value / scale),
                               "base_value": engine.exact_decimal(value)}
                       for name, value in results.items()},
            "total_weight": engine.exact_decimal(weight_total) if wi is not None else None,
            "checks": checks, "passes": all(item["matches"] for item in checks.values())}


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("demo", "check"))
    cli.add_argument("--value-column", default="value")
    cli.add_argument("--weight-column")
    cli.add_argument("--to")
    cli.add_argument("--expect-sum")
    cli.add_argument("--expect-mean")
    cli.add_argument("--expect-weighted-mean")
    args = cli.parse_args(argv)
    if args.command == "demo":
        data = b"distance,weight\n1 km,2\n500 m,1\n"
        args.value_column, args.weight_column, args.to = "distance", "weight", "m"
        args.expect_sum, args.expect_mean, args.expect_weighted_mean = "1500 m", "750 m", "2500 m / 3"
    else:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
    claims = {name: value for name, value in (("sum", args.expect_sum), ("mean", args.expect_mean),
              ("weighted_mean", args.expect_weighted_mean)) if value is not None}
    try:
        result = compute(data, args.value_column, args.weight_column, args.to, claims)
    except TableError as exc:
        print(f"table-flint: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["passes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
