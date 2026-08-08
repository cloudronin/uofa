#!/usr/bin/env python3
"""Freeze the labelled sentences the trained routes learn from.

Ships the DATA, not a fitted model. A pickled sklearn estimator is 1.9 MB and
breaks on the next sklearn release; 9,740 labelled sentences are 0.55 MB
gzipped, survive upgrades, and can be read by a person who wants to know what
the classifier was taught. Given this project's history of numbers that turned
out to measure the tooling, an auditable training set is worth more than a
faster start-up.

Regenerate after any corpus change:

    python dev/tools/scripts/dump_keyless_training.py
"""
from __future__ import annotations

import gzip
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

OUT = _ROOT / "src" / "uofa_cli" / "data" / "keyless_training.jsonl.gz"


def main() -> int:
    from keyless_trained import decision_labels, load, result_labels

    rows = []
    for split in ("train", "holdout"):
        for doc, gt in load(split):
            dpos = set(decision_labels(doc, gt)[0])
            rpos = set(result_labels(doc, gt))
            outcome = (gt.get("expected_decision") or {}).get("outcome")
            n = len(doc.texts)
            for j, t in enumerate(doc.texts):
                rows.append({
                    "t": t,
                    "p": round(j / max(n - 1, 1), 4),   # position, the feature
                    "d": int(j in dpos),                # states the decision
                    "r": int(j in rpos),                # is a validation result
                    "o": outcome if j in dpos else None,
                    "split": split,
                })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    OUT.write_bytes(gzip.compress(body.encode()))
    print(f"  {len(rows)} sentences -> {OUT} ({OUT.stat().st_size / 1e6:.2f} MB)")
    print(f"  positives: decision {sum(r['d'] for r in rows)}, "
          f"results {sum(r['r'] for r in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
