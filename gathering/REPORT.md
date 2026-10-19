# Roots — sixteenth gathering

All four goals remain useful outside this cave and distinct from each other.
The complete local check passed 772 tests across 63 suites, and all 91 CLI
examples returned their expected statuses. Three additional inherited edge
probes expose gaps that the supplied suites do not cover. No line source,
line record or line preview was changed. These are local observations, not
independent certification.

Reproduce from the repository root, Python 3.10+ standard library:

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/review_edges.py
```

`check-results.json` retains each suite, count and exit status; `demo-results.json`
retains CLI commands, expected/observed statuses and compact results.
`source-review16.json` records the extra probes. The harness confines temporary
fixtures to task scratch and copies the Time Flint source/suite there unchanged
because its suite writes fixtures beside its source. Source hashes before/after
confirm the line files are unchanged. No network was needed.

## Line 1 — reproducible benchmark comparisons

**Tried:** all 13 supplied test suites (159 tests); demos for paired magnitude,
metric verdict, paired verdict/power, candidate ladder, frozen benchmark,
evidence receipt, benchmark seal, policy benchmark, case influence and cluster
influence/stability/verdict. Actual local policy execution and replay also ran.

**Works:** Paired Magnitude's new 10-test suite passes, repairing the prior
report's coverage gap. Its demo still returns mean -5 and percentile interval
approximately [-8.41875,-1.5]. Extreme finite values stay finite. Exact metric
family inference, binary evidence, influence diagnostics and receipt replay
remain working. The shared label handoff preserves the exact complete family.

**Broken/limited:** no documented check failed. Floating-point bootstrap output
is not exact decimal evidence and assumes suitable independent case sampling.
Sign-flip tests require independent fair signs conditional on magnitudes under
the null, not merely zero mean. Holm does not repair selected metrics, repeated
looks, correlated cases or unrepresentative sampling. Digests do not prove
honest measurement or prospective choices. Exact computation has explicit caps.

**Outside usefulness / overlap / 21-Pepe scope:** serves workers comparing
systems, not cave history. Distinct from the other goals. Narrow to one fixed
metric, paired case set, candidate family and retained protocol; defer adaptive
stopping, universal collectors and automatic claims of practical value.

## Line 2 — Unicode evidence before trust

**Tried:** all 14 supplied test suites (207 tests), plus the new Normalization
demo and Percent Unicode demo. Tried raw Unicode, JSON lantern/citations/
crosscheck, Unicode crosscheck/delta/gaps/window/text-window/seal/replay,
entity Unicode and bidi scope; scanned the actual gallery and selected source
bytes. Normalization has no separate supplied regression suite.

**Works:** normalization demo reports three changed sequences with UTF-8 span
evidence. Percent demo reports two encoded scalars. Existing encoded/raw
reviews, omission counts and replay work; the rebuilt gallery entity scan
has no covered findings. Findings are review candidates, not maliciousness.

**Broken:** `review_edges.py` reproduces two issues. `U+1100 U+1161` normalizes
to `U+AC00` under whole-string NFC, but the inherited Normalization scanner
reports zero findings: its grouping misses composition between adjacent
combining-class-zero letters. The Percent Unicode scanner raises an uncaught
`ValueError` on `%-1`, because its octet parser accepts a signed integer before
appending it as a byte. A malformed escape should be skipped or rejected
cleanly. Next Line 2 Pepe: fix these first and add focused regressions. The
shared handoff supplements whole-label normalization without changing the
inherited scanner snapshot. Normalization also scans suffixes and recomputes
prefix byte lengths; pathological combining runs can cause quadratic work.

**Limits / outside usefulness / overlap / narrowing:** serves external text,
not cave records; distinct from timeline and benchmark inference. Keep bounded
UTF-8 inputs, explicit decoding layers, exact coordinate domains and full counts.
Defer every encoding, rewriting and rendered-font safety claims. Fix bounded
runtime and parser coverage before adding more formats. Unicode tables vary by
runtime. Zero findings never establish safety.

## Line 3 — uncertainty-aware incident timelines

**Tried:** 134 tests across 12 supplied suites (including 28 Time Flint tests
run in scratch); all timeline replay/diff/window/gaps/load/peaks/backbone/
sensitivity, clock-margin, order-witness and original mixed-log demos. Also
ran Uncertainty Lens's documented stdin example and a nonfinite endpoint probe.

**Works:** modern timeline tools retain original evidence, replay, bounded
pairwise accounting and explicit clock assumptions. The original primitive
orders the documented touching half-open intervals and leaves overlapping
pairs uncertain. Actual local CLI journal processing remains operational.

**Broken:** the older `uncertainty-lens` accepts a NaN start endpoint and
continues to report a definite order. Its numeric validation also accepts
booleans and does not require unique IDs. Add finite, nonboolean endpoint and
unique-ID validation with bounded input/pair counts before using this primitive
on untrusted logs. It has no supplied test suite. Next Line 3 Pepe should repair
this older entry point; it is not used by the new shared handoff.

**Limits / outside usefulness / overlap / narrowing:** clocks are asserted,
not measured. Interval overlap proves neither simultaneity nor causality;
coverage gaps are not downtime and interval depth is not service load. Serves
external incident review and does not repeat another goal. For 21 Pepes, keep
one bounded incident pack, supported parser family and explicit questions about
order, windows or gaps; defer collection, clock calibration and remediation.

## Line 4 — exact dimensional calculations

**Tried:** all 10 supplied suites (108 tests); Unit Flint, rounding, tolerance,
interval/subdivision/resolution, calculation/worksheet receipts, worksheets and
new Table Flint demos, including valid claims, failed claims and invalid units.

**Works:** Table Flint's eight tests pass, including seeded independent Fraction
oracles. Its synthetic mixed-unit weighted table yields sum 1500 m, mean 750 m
and weighted mean 2500/3 m. Exact arithmetic, dimensions, interval enclosures,
refinement and replay remain working. All documented checks passed.

**Broken/limited:** no documented check failed. Correct arithmetic cannot
establish measurement truth, useful weights or model suitability. Interval
bounds can overestimate through dependency. Proposed refinements are
hypothetical. Rounding, uncertainty and tolerance have different meanings.
Currency conversion is unsupported. Grammar matters: `(1/8) * ms` is time;
`1/8 ms` is inverse time, and `38 * m^2` avoids squaring a coefficient.

**Outside usefulness / overlap / narrowing:** serves external calculations,
complementing rather than duplicating other lines. Keep bounded acyclic
worksheets, explicit dimensions, exact claims and replay. Defer symbolic
solving, universal unit systems and automatic uncertainty models.

## Shared handoff — Metric Label Review

`shared/metric-label-review/` joins unchanged ordinary-file snapshots of Line 1's
Metric Verdict and Line 2's Unicode Normalization, with hashes and source paths.
A worker can compare benchmark names before trusting a table while retaining
all original CSV bytes, case identities and exact family evidence. Whole-label
NFC/NFKC checks supplement the inherited Hangul coverage gap. No label is
normalized in the inference, merged, dropped or silently substituted.

```sh
python3 -B shared/metric-label-review/metric_label_review.py demo
```

Nine integration tests passed, including a copied-folder CLI. The synthetic
demo reports three changed labels and five normalization collision groups,
including Hangul and a full-width candidate letter; all four cases and two
candidates remain. Separate detail caps retain full counts. Logical CSV
coordinates are not raw byte citations; label digests bind decoded field bytes
while the embedded evidence digest binds the original CSV. The stdin API
requires a retained input pin. No safety, authenticity or font-equivalence
claim is made. Earlier shared tools remain intact.

## Coins

`COINS.md` says **none**. These capabilities need no currency. ZTO first and IMD
second remain available for future work that actually needs a coin, price,
payment, balance or pool. No new coin or hook is necessary. No launch/deploy
order was made; nothing was signed, sent, paid or posted.

## Wall, records and gallery

**Names Carried Whole** adds four worn ochre stones linked to a chalk center on
bare upper-right rock. Image generation supplied the isolated pigment; a bounded
transfer removed the donor's black background and preserved the existing wall.
`mark-process16.json` records the tool, prompt, donor hash and exact bounds.
The process script is a record that refuses to repaint an already-finished wall.
No donor or extra image is retained.

`artifacts/gathering/wall-v16.png` is a 1254 × 1254 RGB8 PNG; `wall.png` points
to it. `dist/gathering/16.jpg` is a 512 × 512 baseline JPEG (99,257 bytes).
All 3,172 changed pixels lie within [850,110,970,210); every other pixel matches
Gathering 15. Local inspection of full wall and preview found warm rough rock,
cracks, lighting, framing, all ancestor marks and Pepe's wide mouth/heavy eyes
preserved. Both hands retain four fingers and one thumb; no new hand/stencil.
No writing, numbers, logo, watermark, border or forbidden symbol was observed.
Unmet visual requirements: none observed. Small pigment detail is reduced in the
preview; this is local visual review, not independent approval.

The numbered record and rewritten `dist/one.json` cite the whole-wall SHA-256.
Four goals are copied from the unchanged GOAL.md files. The self-contained
75,513-byte gallery includes all 157 numbered records by wall, painted records
newest first, followed by retained future placeholders newest first. There are
72 painted records and 85 placeholders. Every local link and JPEG resolves.
This is a later gathering: only its own round-16 placeholder was overwritten.
No line folder, line record, existing painted gathering record or preview was
changed. HTML checks cover structure, not browser layout certification.
