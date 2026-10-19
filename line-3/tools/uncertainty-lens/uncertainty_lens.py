#!/usr/bin/env python3
"""Summarize which timestamp intervals have a definite order."""
import argparse, json, sys

def analyze(events):
    clean = []
    for item in events:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("each event needs a string id")
        start, end = item.get("start"), item.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or end < start:
            raise ValueError("each event needs numeric start <= end")
        clean.append({"id": item["id"], "start": start, "end": end})
    ordered, uncertain = [], []
    for i, left in enumerate(clean):
        for right in clean[i + 1:]:
            if left["end"] <= right["start"]:
                ordered.append({"before": left["id"], "after": right["id"]})
            elif right["end"] <= left["start"]:
                ordered.append({"before": right["id"], "after": left["id"]})
            else:
                uncertain.append({"events": [left["id"], right["id"]], "reason": "intervals overlap"})
    return {"events": len(clean), "definite_orders": ordered, "uncertain_pairs": uncertain}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", help="JSON array or - for stdin")
    args = ap.parse_args()
    raw = sys.stdin.read() if args.path in (None, "-") else open(args.path, encoding="utf-8").read()
    try:
        result = analyze(json.loads(raw))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"error: {exc}")
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
