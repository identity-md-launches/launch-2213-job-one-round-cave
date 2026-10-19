# Table Flint

Check a CSV table of measured quantities with exact rational arithmetic and
explicit unit dimensions. It calculates the sum, ordinary mean, minimum and
maximum; when a nonnegative dimensionless weight column is supplied, it also
calculates a weighted mean. Rows can use different compatible units. A supplied
claim is compared exactly, and the raw CSV's SHA-256 is included in the result.
This is useful for checking a spreadsheet export before trusting a reported
total or mean. Python 3.10+ and the standard library are the only requirements;
copy this entire folder to use it independently.

From the repository root, **one command shows it working**:

```sh
python3 -B line-4/tools/table-flint/table_flint.py demo
```

Tried locally: the demo exited **0**. Rows of `1 km` with weight `2` and
`500 m` with weight `1` produced exact sum `1500 m`, mean `750 m`, and
weighted mean `2500/3 m`; all three claims matched. These are synthetic
measurements, supplied to show the behavior.

## Check your own CSV

The `check` command reads CSV bytes **only from stdin**. The default value
column is `value`; column names are exact and case sensitive. Each value cell
is a Unit Flint expression such as `1.25 km`, `500 m`, or `3 * (2 m)`.
For example:

```sh
printf 'distance,weight\n1 km,2\n500 m,1\n' | python3 -B line-4/tools/table-flint/table_flint.py check --value-column distance --weight-column weight --to m --expect-sum '1500 m' --expect-weighted-mean '2500 m / 3'
```

Options: `--value-column NAME`, `--weight-column NAME`, `--to UNIT`,
`--expect-sum EXPRESSION`, `--expect-mean EXPRESSION`, and
`--expect-weighted-mean EXPRESSION`. `--to` changes display only; results and
claims are compared in exact base units. A weight must be nonnegative and
dimensionless; at least one must be positive. Zero weights still count in the
ordinary sum and mean. The minimum and maximum are computed from all rows.

Output is JSON. `passes` and each check's `matches` are booleans. **Exit 0**
means every supplied claim matched (or no claims were supplied). **Exit 1**
means the table was valid but a claim failed; the computed result is still
printed. **Exit 2** means invalid input, with no partial result on stdout.

The CSV is UTF-8 (an optional UTF-8 BOM is accepted), with a header and 1–4096
data rows, at most 16 distinct nonempty columns, and a 262,144-byte input
limit. Every row must have the header's column count. The exact expression
parser supports `+ - * / ^ **`, parentheses, decimal/scientific numbers and
integer powers from -12 to 12. Its units include length, mass, time, data,
volume, force, energy and power. Expressions have a 4096-character, 256-token,
32-level and 2048-bit arithmetic budget. No row with an incompatible dimension
is silently skipped. Rows are never rounded before aggregation.

The SHA-256 identifies the input bytes for comparison with a separately retained
CSV; it is not an authorship signature. The tool cannot establish whether the
measurements, weights, formula or claims are true. It does not read files named
in CSV, use a network, sign or send transactions, or infer currency exchange
rates. Numerical table checking needs no coin or price; ZTO/IMD values were
not invented.

Run the regression suite:

```sh
python3 -B -m unittest discover -s line-4/tools/table-flint -v
```

Locally, eight tests passed, including 100 seeded tables checked against an
independent `Fraction` oracle, mixed units, weight edge cases, malformed CSV,
input limits, incompatible dimensions and real CLI exit statuses. A standalone
copy of this folder also passed all eight tests and the demo. `engine.py`
is an unchanged ordinary-file snapshot of Unit Flint; it requires no installed
dependency or symlink to another tool.
