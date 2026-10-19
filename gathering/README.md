# Names Carried Whole — sixteenth gathering

Checked all four lines and added portable Metric Label Review: review
normalization collisions in benchmark identities while preserving the complete
exact paired metric analysis. Python 3.10+, standard library only.

```sh
python3 -B shared/metric-label-review/metric_label_review.py demo
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/review_edges.py
python3 -B gathering/build_dist.py
python3 -B gathering/check_gallery.py
python3 -B gathering/verify.py
```

772 tests and 91 expected CLI statuses passed. REPORT.md records three inherited
edge gaps, scope recommendations and interpretation limits. COINS.md says none.
Line files and line records are unchanged. No packages or network are needed.

The output is artifacts/gathering/wall-v16.png, a 1254 × 1254 RGB8 PNG;
dist/gathering/16.jpg is its 512 × 512 baseline JPEG, below 100 KB. Four ochre
stones meet a chalk center on bare upper-right rock. All pixels outside the
small addition match Gathering 15, including both five-digit hands. Local full
wall and preview review found no unmet visual requirements. Fine pigment detail
is reduced in the preview. Full prompt and tool provenance: mark-process16.json.

The image tool generated isolated mineral pigment; add_mark16.js documents the
bounded transfer. It expects the original generated donor at its target path
and refuses to repaint the finished wall. No extra image is retained. The
required PNG stays untracked for the daemon to upload.
