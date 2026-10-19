# Uncertainty Lens

Uncertainty Lens turns a small JSON list of timestamp intervals into a
reproducible summary of definite pairwise order and pairs whose intervals
overlap. It is a local, read-only incident-evidence helper: it never executes
the services described by the events and uses only Python's standard library.

Try it from the repository root:

```sh
printf '%s\n' '[{"id":"ingest","start":1,"end":3},{"id":"alert","start":3,"end":4},{"id":"retry","start":2,"end":5}]' | python3 line-3/tools/uncertainty-lens/uncertainty_lens.py
```

The command reports `ingest` before `alert`, while identifying the overlapping
pairs as uncertain. Input intervals are half-open: an end exactly equal to a
later start is a definite order. The tool does not infer causality or resolve
an overlap from event names.
