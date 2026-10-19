# Unicode Normalization

Expose Unicode text whose canonical or compatibility-normalized form differs
from the original, with exact UTF-8 byte evidence. This helps a worker review
identifiers that can look stable in one representation but change under a
normalizing system. Python 3.10+ and the standard library are sufficient; the
tool has no network, dependency, environment, sibling-import, or file-writing
behavior.

Run this one command from the repository root:

```sh
python3 -B line-2/tools/unicode-normalization/unicode_normalization.py --demo
```

The demo reports three synthetic normalization findings: a full-width ASCII
letter, a Kelvin sign, and a circled digit. The demo is labeled synthetic,
not an observed attack. For a real, explicitly selected workspace file:

```sh
python3 -B line-2/tools/unicode-normalization/unicode_normalization.py --file path/to/text.txt
```

Each finding gives the original escaped text, NFC and NFKC forms, scalar names,
the original UTF-8 byte range, and a SHA-256 of that exact source span. Counts
cover the complete input even when `--max-details` limits retained evidence.
Normalization is not inherently malicious, so findings require human review;
the tool does not render text or claim that two fonts will look alike. Inputs
must be strict UTF-8 regular files inside the current workspace and at most
2 MiB. It emits escaped ASCII JSON and never rewrites the selected file.

Observed locally: the demo completed successfully with three findings and
Unicode database version reported by the active Python runtime.
