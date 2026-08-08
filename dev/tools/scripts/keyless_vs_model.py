#!/usr/bin/env python3
"""The head-to-head: keyless against the model extractor, same documents, same gold.

Step 4 of the keyless plan says measure before making anything the default. This
is that measurement, and it is deliberately the only place the two are compared
-- scoring them in separate scripts is how router recall came to be reported as
an end-to-end result.

## What can honestly be compared, and what cannot

**Validation results, 24 annotated across all five papers.** Gold is a verbatim
span, both extractors emit text, and matching is keyword containment. Clean.

**Factor levels are NOT compared, and the reason matters.** The real papers record
a letter gradation within a stated range -- `b` of `a-c` -- while the extractors
emit integers on the template's 1-4 scale. Mapping one onto the other requires a
judgement about what "b of a-c" means as a number, and a wrong mapping produces a
confident figure that measures the mapping. This project has produced ten of
those. So the levels are reported as FILLED or BLANK, which is a fact, and not as
correct or incorrect, which would be a guess.

**Groundedness replaces it.** Every rationale the model writes is checked against
the source text with the project's existing scorer. That needs no scale mapping,
and it answers the question a default actually turns on: of the material the
model adds and keyless does not, how much is supported by the document?

Context of use has gold on **one** paper, so it is reported and not concluded
from.

## The control is in the table

`control_constant_list` -- print the standard's checklist, read nothing -- scores
1.000 on factor DETECTION on this corpus. So detection is not reported here at
all; only whether the value matches the gold.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

REAL = [
    ("opensim", "extract_corpus_real/bundle_real_opensim_knee"),
    ("bologna", "extract_corpus_vv40/bundle_bologna_bcthip"),
    ("nagaraja", "extract_corpus_vv40/bundle_nagaraja"),
    ("elemance", "extract_corpus_real/bundle_real_elemance_thoracic"),
    ("morrison", "extract_corpus_vv40/bundle_morrison"),
]


def _norm(s) -> str:
    return " ".join(str(s or "").split()).lower()


def _rows_from_xlsx(path: pathlib.Path) -> dict:
    """Read an extraction workbook back.

    The header is NOT the first non-empty row: row 1 is a title, row 2 an
    instruction, row 3 the header and row 4 help text. Taking the first non-empty
    row produced "factor names" like "complete profile only. assess each relevant
    factor..." -- a reader that returns confident nonsense.
    """
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {"validation": [], "factors": {}, "rationales": []}
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        hdr_i = next((i for i, r in enumerate(rows)
                      if any(_norm(c) == "factor type" for c in r)
                      or any(_norm(c) in ("name", "result name") for c in r)), None)
        if hdr_i is None:
            continue
        header = [_norm(c) for c in rows[hdr_i]]
        for r in rows[hdr_i + 1:]:
            rec = {h: v for h, v in zip(header, r) if h}
            if all(v in (None, "") for v in r):
                continue
            if "validation" in ws.title.lower():
                out["validation"].append(
                    " ".join(str(v) for v in r if isinstance(v, str)))
            elif "credibility" in ws.title.lower():
                name = _norm(rec.get("factor type"))
                if not name or name.startswith(("v&v 40 factor", "nasa")):
                    continue      # the help-text row
                out["factors"][name] = rec.get("achieved level")
                rat = rec.get("rationale")
                if isinstance(rat, str) and len(rat) > 20:
                    out["rationales"].append(rat)
    return out


def _valresult_gold(tag: str) -> list[list[str]]:
    p = _ROOT / "docs" / "v1" / f"valresults_{tag}.json"
    if not p.exists():
        return []
    return [[w for w in re.findall(r"[A-Za-z0-9.%±]+", r["span"]) if len(w) > 2][:6]
            for r in json.loads(p.read_text())["results"]]


def _source_text(rel: str) -> str:
    """The document itself, read the way the extractor read it."""
    from uofa_cli.document_reader import discover_files, read_corpus
    src = _ROOT / "tests" / "fixtures" / rel / "source"
    files, _warnings = discover_files([src])   # returns (files, warnings)
    corpus = read_corpus(files)
    return "\n".join(c.text for c in corpus.chunks)


def score(book: dict, tag: str, rel: str, source: str) -> dict:
    """The same function for both extractors, by construction.

    Three quantities, and each is the kind of thing it says it is:
    a HIT against gold, a COUNT of what was filled, and a groundedness RATE.
    """
    from groundedness import score_factor_rationales

    joined = _norm(" ".join(book["validation"]))
    vg = _valresult_gold(tag)
    vhit = sum(1 for kws in vg
               if kws and sum(_norm(k) in joined for k in kws) >= max(2, len(kws) - 2))

    filled = sum(1 for v in book["factors"].values() if v not in (None, ""))

    # Groundedness of what was written: are the numbers in each rationale
    # actually in the document? Keyless writes none, so it has nothing to be
    # ungrounded about -- which is the trade being measured, not a free win.
    # `rationale` must be a plain string: the scorer checks isinstance(str) and
    # silently skips anything else, so wrapping it in {"value": ...} produced a
    # confident 0/0 rather than an error.
    facs = [{"rationale": r, "factor_type": ""} for r in book["rationales"]]
    g = score_factor_rationales(facs, source) if facs else None
    return {"vr_hit": vhit, "vr_n": len(vg),
            "levels_filled": filled, "levels_n": len(book["factors"]),
            "claims": g.claims_total if g else 0,
            "grounded": g.claims_grounded if g else 0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model-dir", type=pathlib.Path, required=True,
                    help="directory of <tag>.xlsx from the paid run")
    ap.add_argument("--keyless-dir", type=pathlib.Path, required=True)
    args = ap.parse_args()

    print("\nKeyless vs model — the five real papers, gpt-5\n")
    print(f"  {'paper':10s}{'val results (gold/model/keyless)':>34s}"
          f"{'levels filled':>16s}{'rationale claims grounded':>28s}")
    T = {k: 0 for k in ("vr_n", "vr_m", "vr_k", "lm", "lk", "ln",
                        "cm", "gm", "ck", "gk")}
    for tag, rel in REAL:
        mp, kp = args.model_dir / f"{tag}.xlsx", args.keyless_dir / f"{tag}.xlsx"
        if not (mp.exists() and kp.exists()):
            print(f"  {tag:10s}{'(workbook missing — NOT counted)':>34s}")
            continue
        source = _source_text(rel)
        m = score(_rows_from_xlsx(mp), tag, rel, source)
        k = score(_rows_from_xlsx(kp), tag, rel, source)
        print(f"  {tag:10s}{m['vr_n']:>14d}{m['vr_hit']:>10d}{k['vr_hit']:>10d}"
              f"{m['levels_filled']:>9d}/{k['levels_filled']:<6d}"
              f"{m['grounded']:>14d}/{m['claims']:<6d}"
              f"{k['grounded']:>3d}/{k['claims']:<4d}")
        for dst, val in (("vr_n", m["vr_n"]), ("vr_m", m["vr_hit"]),
                         ("vr_k", k["vr_hit"]), ("lm", m["levels_filled"]),
                         ("lk", k["levels_filled"]), ("ln", m["levels_n"]),
                         ("cm", m["claims"]), ("gm", m["grounded"]),
                         ("ck", k["claims"]), ("gk", k["grounded"])):
            T[dst] += val

    vr_n = max(T["vr_n"], 1)
    print("\n  ── validation results, the one dimension with gold on all five ──")
    print(f"     model    {T['vr_m']:>3d}/{T['vr_n']:<3d}  {T['vr_m']/vr_n:.3f}")
    print(f"     keyless  {T['vr_k']:>3d}/{T['vr_n']:<3d}  {T['vr_k']/vr_n:.3f}")

    print("\n  ── factor levels: reported as filled, not as correct ──")
    print(f"     model    {T['lm']:>3d}/{T['ln']:<3d} filled")
    print(f"     keyless  {T['lk']:>3d}/{T['ln']:<3d} filled  (none, by design)")
    print("     The papers grade a letter within a range ('b' of 'a-c'); the")
    print("     template takes an integer. Scoring one against the other would")
    print("     measure the mapping I chose, so it is not scored.")

    print("\n  ── groundedness of what each WROTE ──")
    if T["cm"]:
        print(f"     model    {T['gm']}/{T['cm']} numeric claims in its rationales "
              f"appear in the source  ({T['gm']/T['cm']:.3f})")
    print(f"     keyless  {T['ck']} claims — it writes no rationales, so it has "
          f"none to ground")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
