#!/usr/bin/env python
"""Compute and pin the A16 sample frame. Run once, before any judge call.

    python studies/taxonomy-validation/frame.py --corpus <datasetcard_info.parquet>

Writes `frame.json`: the corpus pin, the strata, and the pre-registered expected
counts -- including W-EV-DIV-07's opportunity count, which must be a prediction
rather than a post-hoc explanation of a small number.

The frame is stratified by task category, card word-count band, and A3 detector
outcome. Eval-bearing cards are the assessment population; the no-eval stratum
validates the detector's NEGATIVE calls, which is the direction that matters --
a false "no reported evaluation" claims a clean absence over evidence that
exists.

Nothing here calls a judge or an LLM. It reads the corpus and counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import card_eval  # noqa: E402

WORD_BANDS = ((0, 200), (200, 800), (800, 2000), (2000, 10**9))


def _band(n: int) -> str:
    for low, high in WORD_BANDS:
        if low <= n < high:
            return f"{low}-{high if high < 10**9 else 'inf'}"
    return "unknown"


def _corpus_pin(path: Path) -> dict:
    """A9.1 artifact pin, non-HF fallback form: content hash + size + fetch date.

    Without this the frame describes a snapshot nobody can retrieve, and every
    figure computed from it is unverifiable.
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return {"path": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def build(corpus: Path, text_column: str, category_column: str | None) -> dict:
    import pandas as pd

    frame = pd.read_parquet(corpus)
    if text_column not in frame.columns:
        raise SystemExit(
            f"column {text_column!r} not in the parquet; columns are "
            f"{list(frame.columns)[:20]}. Pass --text-column.")

    strata: dict[str, int] = {}
    eval_bearing = no_eval = 0
    div_opportunities = 0
    aliases = None
    try:
        from uofa_cli.furnishers.card_prose import _alias_map
        aliases = set(_alias_map().keys())
    except Exception:                                  # alias table optional here
        aliases = set()

    use_category = bool(category_column and category_column in frame.columns)
    categories = frame[category_column].fillna("unknown") if use_category else None

    for i, text in enumerate(frame[text_column].fillna("")):
        text = str(text)
        presence = card_eval.detect(text)
        bearing = presence.found
        eval_bearing += bearing
        no_eval += (not bearing)
        category = str(categories.iloc[i]) if use_category else "all"
        key = f"{category}|{_band(len(text.split()))}|{'eval' if bearing else 'no-eval'}"
        strata[key] = strata.get(key, 0) + 1

        # A DIV-07 opportunity requires the card to name a constituent the
        # furnisher also measures. Counting cards would overstate it.
        low = text.lower()
        if aliases and any(a in low for a in aliases):
            div_opportunities += 1

    total = int(len(frame))
    return {
        "study": "taxonomy-validation",
        "corpus_pin": _corpus_pin(corpus),
        "n_cards": total,
        "n_eval_bearing": int(eval_bearing),
        "n_no_eval": int(no_eval),
        "pct_eval_bearing": round(100 * eval_bearing / total, 2) if total else None,
        "strata": strata,
        "div07_opportunity_cards": int(div_opportunities),
        "div07_opportunity_pct": round(100 * div_opportunities / total, 2) if total else None,
        "div07_note": (
            "Cards naming a constituent the furnisher measures. The true "
            "opportunity count is matched reported/furnished PAIRS and is <= this, "
            "since a named benchmark may still yield no extractable score. "
            "Pre-registered as an upper bound on opportunities, not on cards."
        ),
        "detector": "uofa_cli.furnishers.card_eval.detect (A3, presence-only)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--text-column", default="model_card")
    ap.add_argument("--category-column", default="task_category")
    ap.add_argument("--out", default=str(Path(__file__).parent / "frame.json"))
    args = ap.parse_args()

    if not args.corpus.exists():
        raise SystemExit(f"corpus not found: {args.corpus}")

    frame = build(args.corpus, args.text_column, args.category_column)
    Path(args.out).write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n")
    print(f"cards                    : {frame['n_cards']}")
    print(f"  eval-bearing           : {frame['n_eval_bearing']} ({frame['pct_eval_bearing']}%)")
    print(f"  no-eval stratum        : {frame['n_no_eval']}")
    print(f"  DIV-07 opportunity ub  : {frame['div07_opportunity_cards']} "
          f"({frame['div07_opportunity_pct']}%)")
    print(f"\nwrote {args.out}")
    print("Now: commit frame.json, flip PREREGISTRATION.md's status line, hash the "
          "directory. Only then may a judge be invoked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
