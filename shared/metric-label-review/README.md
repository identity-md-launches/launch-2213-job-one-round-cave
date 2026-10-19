# Metric Label Review

Review the identity labels in a continuous-metric CSV before relying on a
benchmark table. This portable folder joins Line 1's exact Metric Verdict with
Line 2's Unicode Normalization evidence. Python 3.10+ and the standard library
are sufficient. No installation, network or sibling folder is needed.

From the repository root:

```sh
python3 -B shared/metric-label-review/metric_label_review.py demo
```

Observed: the synthetic four-case, two-candidate CSV has three labels that
change under normalization and five collision groups: one candidate-header
NFKC group and two case-ID groups under each of NFC and NFKC. It includes a
full-width letter, composed/decomposed accent and Hangul Jamo composition.
All four cases and both candidates remain in the original exact analysis.
No real system performance or attack is claimed.

For your own CSV, retain its lowercase SHA-256 independently and pass the
original bytes on stdin:

```sh
python3 -B shared/metric-label-review/metric_label_review.py review \
  --expected-input-sha256 YOUR_RETAINED_SHA256 < YOUR_SELECTED_CSV
```

Header: `case,baseline,candidate-name` with up to 16 candidates and 2–200
cases; plain decimal measurements have at most six fractional digits. All
Metric Verdict validation and exact-work caps apply. The CLI reads at most
2 MiB plus one byte. `--better lower|higher` and `--alpha` are passed unchanged
to that engine. `--max-details 0..1000` caps changed-label details and collision
groups separately; their complete counts and original evidence remain.

Review compares whole labels under NFC and NFKC and groups collisions within
headers and case IDs separately. It does not rewrite names, merge cases or
select candidates. The inherited sequence scanner is also run on each changed
label, retaining its total count, which can be zero for Hangul composition.
Whole-label comparison supplements that known upstream coverage gap. No
original-CSV byte-span citation is claimed: coordinates identify logical CSV
records and columns, including CSV quoting and an optional BOM. Label digests
bind the decoded field's UTF-8 bytes; the evidence digest binds the raw CSV.

Exit 0 means a completed review, including when review is required or a
statistical test does not reject. Exit 2 means invalid input, empty stdout and
an ASCII-escaped diagnostic. Output is ASCII JSON. No file named by input is
opened, and no file is written. Labels are not redacted; JSON escaping does not
make them safe to insert as HTML.

Normalization differences may be legitimate. This checks neither font
confusables nor rendered identity, deception or safety. Runtime Unicode tables
are reported and can change results. Pins establish byte identity, not truth,
authorship or preregistration. The embedded exact sign-flip analysis requires
independent fair signs conditional on magnitudes under its null; zero mean or
independent cases alone do not suffice. Freeze the metric, units, cases,
family, direction and analysis before seeing outcomes. Non-rejection does not
establish equivalence, and label review supplies no statistical guarantee.

Two byte-identical ordinary-file engine snapshots ship in `engines/`, with
original paths and hashes in `provenance.json`. Nothing uses an environment,
key, wallet, signature, payment or posting.

```sh
python3 -B -m unittest discover -s shared/metric-label-review -v
```

Nine tests passed: composed/decomposed and Hangul collisions, unchanged exact
family inference in both directions, plain labels, caps, header/case scope
separation, BOM/CRLF/quoted fields, digests, malformed inputs, snapshot identity
and successful/invalid copied-folder CLI runs. Tests use only task scratch.
