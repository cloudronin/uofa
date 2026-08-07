#!/usr/bin/env python3
"""The three acceptance measures `corpus_profile.py` cannot compute offline.

    factor selection   real 0.920   band 0.85-0.95
    same sentence      real 0.714   band 0.60-0.85
    N/A rate           real 0.000   must be exactly 0

Separate from `d1_annotator_agreement.py` on purpose: that script is the record
of a completed measurement on the five real papers, with its documents and its
annotations fixed. Repointing it at a generated corpus would overwrite the
baseline these bands are anchored to. The protocol -- prompt, scope block,
span-to-sentence matching -- is imported from it so the two stay comparable.

## Why the high side of the band is the point

The seeded pilot scored **1.000** on factor selection against a real 0.920. A
one-sided gate would have called that the best result in the run. It is the
opposite: papers everyone agrees about are papers that report a clean finding for
every factor, which is what the old corpus did and what R5 exists to stop. Above
the band fails.

## Cross-family, enforced

Gold is written by one model family and this check must come from another. Same
family twice measures determinism, not reliability -- which is what made the
circularity result (76.9% against a 71.4% real baseline, Fisher p = 1.000) mean
anything.

## No verdict without data

An earlier version of the D1 script printed "< 0.60: largely one reader's
judgement" when both API calls had returned nothing. An API failure is not
evidence about a corpus.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from d1_annotator_agreement import PROMPT, norm, spans_for, toks  # noqa: E402
from document_furniture import strip_furniture  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

BANDS = {"agree_selection": (0.85, 0.95), "agree_same_sentence": (0.60, 0.85),
         "na_rate": (0.0, 0.0)}
_NA = {"n/a", "na", "not applicable", "none", "null", ""}


def _family(model: str) -> str:
    return "anthropic" if model.split("/")[-1].startswith("claude") else "openai"


def main() -> int:
    from uofa_cli.llm.backend import GenerationOptions
    from uofa_cli.llm.litellm_backend import LiteLLMBackend

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--model", default="claude-sonnet-4-6",
                    help="the SECOND annotator; must differ in family from the "
                         "model that wrote the gold")
    ap.add_argument("--key-file", type=pathlib.Path, default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-scopes", type=int, default=3,
                    help="scopes annotated per bundle (each is one call carrying "
                         "the whole document). 3 gives ~55 factor comparisons "
                         "across 3 bundles, against D1's 42 on the real corpus; "
                         "all 22 scopes would cost ~$2 to measure the same thing.")
    args = ap.parse_args()

    bundles = sorted(b for b in args.corpus.rglob("bundle_*")
                     if (b / "ground_truth.json").exists())
    if not bundles:
        raise SystemExit(f"no bundles with ground_truth.json under {args.corpus}")
    bundles = bundles[:args.limit] if args.limit else bundles

    gold_models = {json.loads((b / "ground_truth.json").read_text()).get("gold_model")
                   or _gold_model_from_report(args.corpus) for b in bundles}
    for gm in gold_models:
        if gm and _family(gm) == _family(args.model):
            raise SystemExit(
                f"gold was written by {gm!r} and this check uses {args.model!r} "
                "-- same family. That measures determinism, not reliability.")

    fam = _family(args.model)
    var = "ANTHROPIC_API_KEY" if fam == "anthropic" else "OPENAI_API_KEY"
    if not os.environ.get(var) and args.key_file and args.key_file.exists():
        os.environ[var] = args.key_file.read_text().strip()
    if not os.environ.get(var):
        raise SystemExit(f"{var} not set (and no readable --key-file)")

    backend = LiteLLMBackend(backend_name=fam if fam == "openai" else "anthropic",
                             model_name=args.model, api_key=os.environ[var],
                             default_timeout_seconds=300)

    failed, tot_f, both_f = [], 0, 0
    tot_s = agree_s = 0
    na_total = na_hits = 0
    print(f"\nseeded agreement — {len(bundles)} bundles, second annotator "
          f"{args.model} ({fam})\n")

    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        pdfs = sorted((b / "source").glob("*.pdf"))
        if not pdfs:
            continue
        text = "\n".join(c.text for p in pdfs for c in read_pdf(p))
        sents = sentences(text)
        kept, _, _ = strip_furniture(sents, NAMES)

        findings = gt.get("findings", [])
        na_total += len(findings)
        na_hits += sum(1 for f in findings
                       if str(f.get("level", "")).strip().lower() in _NA)

        # One scope at a time. Withholding it manufactured a 1/6 disagreement in
        # D1 -- the annotator quoted the right factor for the wrong model.
        by_scope: dict[tuple[str, str], dict[str, list[str]]] = {}
        for f in findings:
            if f.get("status") == "ambiguous":
                continue
            key = (f.get("model", ""), f.get("mechanism", ""))
            by_scope.setdefault(key, {}).setdefault(f["factor"], []).append(f["span"])

        # Largest scopes first: a scope with one finding contributes almost
        # nothing to the estimate and costs the same as one with eight.
        chosen = sorted(by_scope.items(), key=lambda kv: -len(kv[1]))[:args.max_scopes]
        if len(chosen) < len(by_scope):
            print(f"    (annotating {len(chosen)} of {len(by_scope)} scopes; "
                  f"the rest are not measured)")
        for (model, mech), mine in chosen:
            scope = (f"This assessment is specifically of -- model: {model}; "
                     f"mechanism: {mech}.\n")
            raw = backend.generate(
                PROMPT.format(factor_list="\n".join(f"- {x}" for x in ec.VV40_FACTOR_NAMES),
                              source="\n".join(kept)[:80000], scope=scope),
                GenerationOptions(max_tokens=16000))
            m = re.search(r"\{.*\}", raw or "", re.S)
            if not m:
                failed.append(f"{b.name}[{model}/{mech}]")
                continue
            try:
                theirs = {f["factor_type"]: f.get("evidence") or []
                          for f in json.loads(m.group(0)).get("factors", [])
                          if f.get("evidence")}
            except json.JSONDecodeError:
                failed.append(f"{b.name}[{model}/{mech}]")
                continue

            for f in set(mine) | set(theirs):
                tot_f += 1
                if f in mine and f in theirs:
                    both_f += 1
                    ms, ts = spans_for(mine[f], sents), spans_for(theirs[f], sents)
                    if ms and ts:
                        tot_s += 1
                        agree_s += 1 if ms & ts else 0
        print(f"  {b.name:30s} {len(by_scope)} scopes, {len(findings)} findings")

    if failed or tot_f == 0:
        print("\n  ── DID NOT RUN ──")
        print(f"  no usable response: {failed or 'none'};  comparable factors: {tot_f}")
        print("  No verdict. An API failure is not evidence about the corpus.")
        return 1

    got = {"agree_selection": both_f / tot_f,
           "agree_same_sentence": agree_s / max(tot_s, 1),
           "na_rate": na_hits / max(na_total, 1)}
    print()
    bad = []
    for k, (lo, hi) in BANDS.items():
        v = got[k]
        ok = lo - 1e-9 <= v <= hi + 1e-9
        bad += [] if ok else [k]
        print(f"  {'PASS' if ok else 'FAIL'}  {k:22s} {v:6.3f}   band [{lo:.2f}, {hi:.2f}]")
    if got["agree_selection"] > BANDS["agree_selection"][1]:
        print("\n  Selection is ABOVE the band. That is a failure, not a good "
              "result:\n  every factor is cleanly reported, which is the old "
              "corpus's defect.\n  R5 (omitted and ambiguous factors) is what "
              "brings it down.")
    if bad:
        print(f"\n  OUT OF TOLERANCE: {bad}")
    return 1 if bad else 0


def _gold_model_from_report(corpus: pathlib.Path) -> str | None:
    r = corpus / "generation_report.json"
    return json.loads(r.read_text()).get("gold_model") if r.exists() else None


if __name__ == "__main__":
    raise SystemExit(main())
