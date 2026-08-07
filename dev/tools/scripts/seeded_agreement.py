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
from uofa_cli.adversarial.model_costs import estimate_cost  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

# Anchored on the five real papers, measured 2026-08-07 by running
# d1_annotator_agreement.py: 77 (document, factor) cells, 49 marked by both,
# 1 gold-only, 1 annotator-only, 26 by neither.
#
#     Jaccard   0.961        Gwet AC1  0.952        same-sentence 0.708
#
# The ceiling was 0.95 and the real corpus measures 0.961 -- the band rejected
# its own reference. The old anchor of "real 0.920" came from a D1 run predating
# two fixes to that script (a table-bias in the annotation, and withheld scope).
# Ceilings now sit above the real value and below 1.000, which is what the old
# synthetic corpus and the first seeded paper both scored.
BANDS = {"agree_selection": (0.85, 0.99), "agree_selection_ac1": (0.85, 0.99),
         "agree_same_sentence": (0.60, 0.85), "na_rate": (0.0, 0.0)}
REAL = {"agree_selection": 0.961, "agree_selection_ac1": 0.952,
        "agree_same_sentence": 0.708, "na_rate": 0.0}


def gwet_ac1(both_yes: int, gold_only: int, annot_only: int, neither: int) -> float:
    r"""Chance-corrected agreement that survives high prevalence.

    Cohen's kappa is the usual instrument and is unusable here. Measured on the
    real papers it returns **0.000 for bologna and nagaraja despite 92% raw
    agreement**, because one rater marked 100% of the checklist and a rater with
    no variance carries no information for kappa however well they agree. That is
    the kappa paradox (Feinstein & Cicchetti 1990).

    Here it is structural rather than unlucky. R8 records that real credibility
    assessments enumerate the whole checklist and score absent evidence 0 rather
    than dropping the row, so prevalence is near 100% by the nature of the
    artefact -- the same property that makes `control_constant_list` score 1.000.

    Gwet's AC1 estimates chance agreement from how often the raters were in the
    ambiguous middle rather than from their marginals, so it does not collapse
    when nearly everything is marked.
    """
    n = both_yes + gold_only + annot_only + neither
    if n == 0:
        return float("nan")
    po = (both_yes + neither) / n
    pi = ((both_yes + gold_only) / n + (both_yes + annot_only) / n) / 2
    pe = 2 * pi * (1 - pi)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")
# "not stated" belongs here. It is what N/A means, and leaving it out let a run
# where 188 of 207 levels were "not stated" score na_rate 0.000 and pass -- the
# check would have been satisfied by the wording of the failure.
_NA = {"n/a", "na", "not applicable", "none", "null", "not stated",
       "unspecified", "unknown", ""}


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
    ap.add_argument("--save-raw", type=pathlib.Path, default=None,
                    help="dump the annotator's responses; without them every "
                         "diagnosis of a failing score costs another full run")
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

    # Priced, because an unpriced check is a hole in the same spend guard the
    # generator has: two earlier runs of this script cost real money that
    # could only be estimated afterwards.
    spent_tokens = 0
    failed, tot_f, both_f = [], 0, 0
    gold_only = annot_only = annot_out_of_scope = 0
    # Document level is the GATED basis, because that is how D1 measured the
    # numbers the bands are anchored to: one comparison per (document, factor),
    # pooling every scope. Measuring per (model x mechanism) and comparing
    # against a document-level band scored this corpus at 0.508 against a real
    # 0.708 -- a granularity mismatch reported as a corpus defect.
    #
    # An earlier explanation for that gap, that more scopes per paper make
    # attribution harder, was tested against the real papers and REFUTED:
    # elemance has 8 scopes and the highest same-sentence agreement of the five
    # (6/6), while single-scope bologna has the lowest (7/12).
    doc_gold: dict = {}
    doc_annot: dict = {}
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

        # The annotator gets the vocabulary of the bundle's OWN standard. D1
        # records this and the reason -- "offering the wrong list guarantees
        # disagreement on factor selection for reasons that have nothing to do
        # with reading" -- and this script imported D1's prompt without its
        # constraint, hardcoding V&V 40 names. On a 7009A bundle only 4 of 14
        # gold factors were even on the list offered, and selection agreement
        # came out at 0.184: a vocabulary mismatch reported as a reading
        # disagreement.
        vocab = (list(ec.VV40_FACTOR_NAMES) if gt.get("standard") == "V&V40"
                 else list(ec.NASA_ALL_FACTOR_NAMES))

        # Both sides must be judged on the same basis. Gold's out-of-scope
        # findings are dropped at generation time, because the plan forbids the
        # factor and the authored table does not contain it -- the paper makes no
        # claim about it. The annotator is deliberately NOT told the scope, so it
        # still selects those factors, and counting them as disagreement measures
        # the constraint rather than the reading: one run scored 0.467 with gold a
        # strict subset of the annotator, 0 gold-only against 65 annotator-only.
        #
        # They are excluded and COUNTED, never silently dropped. The count is
        # itself a result: it says how often a careful reader attributes a factor
        # this paper does not assess.
        paper_scope = {x.lower() for x in gt.get("scope_allowed", [])}

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
            # Every reference span, not just the first. The key is
            # multi-reference because these papers state a finding more than
            # once; scoring against one arbitrary member of that set measures
            # which member gold happened to list first.
            spans = f.get("spans") or ([f["span"]] if f.get("span") else [])
            by_scope.setdefault(key, {}).setdefault(f["factor"], []).extend(spans)

        # Largest scopes first: a scope with one finding contributes almost
        # nothing to the estimate and costs the same as one with eight.
        chosen = sorted(by_scope.items(), key=lambda kv: -len(kv[1]))[:args.max_scopes]
        if len(chosen) < len(by_scope):
            print(f"    (annotating {len(chosen)} of {len(by_scope)} scopes; "
                  f"the rest are not measured)")
        for (model, mech), mine in chosen:
            scope = (f"This assessment is specifically of -- model: {model}; "
                     f"mechanism: {mech}.\n")
            prompt_text = PROMPT.format(
                factor_list="\n".join(f"- {x}" for x in vocab),
                source="\n".join(kept)[:80000], scope=scope)
            raw = backend.generate(prompt_text, GenerationOptions(max_tokens=16000))
            spent_tokens += len(prompt_text) // 4 + len(raw or "") // 4
            if args.save_raw:
                args.save_raw.mkdir(parents=True, exist_ok=True)
                (args.save_raw / f"{b.name}.{abs(hash((model, mech))) % 9999}.json"
                 ).write_text(raw or "")
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

            for f, sp in mine.items():
                doc_gold.setdefault(b.name, {}).setdefault(f, []).extend(sp)
            for f, sp in theirs.items():
                doc_annot.setdefault(b.name, {}).setdefault(f, []).extend(sp)

            for f in set(mine) | set(theirs):
                if paper_scope and f.lower() not in paper_scope:
                    annot_out_of_scope += 1
                    continue
                tot_f += 1
                if f in mine and f not in theirs:
                    gold_only += 1
                elif f in theirs and f not in mine:
                    annot_only += 1
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

    # WHICH WAY the disagreement runs. A single agreement figure cannot tell a
    # corpus that is genuinely ambiguous from a protocol where one side is
    # simply more liberal -- gold is asked to enumerate every
    # (model x mechanism x factor), the annotator to judge what the paper
    # reports, and those are not the same task.
    print(f"\n  gold selected but annotator did not: {gold_only}")
    print(f"  annotator selected but gold did not:  {annot_only}")
    print(f"  both:                                 {both_f}   of {tot_f}")
    print(f"  annotator picked a factor the paper does not assess: "
          f"{annot_out_of_scope} (excluded from the score, not hidden)")

    cost = estimate_cost(args.model, spent_tokens, output_ratio=0.08)
    print(f"\n  {spent_tokens:,} tokens, about ${cost:.2f}")

    # Recompute at document level -- the basis the bands come from.
    d_both = d_uni = d_hit = d_tot = 0
    ac_by = ac_go = ac_ao = ac_nn = 0   # the 2x2 AC1 needs
    for name in doc_gold:
        gt2 = json.loads((args.corpus / name / "ground_truth.json").read_text()) \
            if (args.corpus / name / "ground_truth.json").exists() else \
            json.loads(next(args.corpus.rglob(f"{name}/ground_truth.json")).read_text())
        sc = {x.lower() for x in gt2.get("scope_allowed", [])}
        sents = sentences("\n".join(c.text for p in sorted((args.corpus / name).rglob("*.pdf"))
                                     for c in read_pdf(p)))
        g = {k: v for k, v in doc_gold[name].items() if not sc or k.lower() in sc}
        t = {k: v for k, v in doc_annot.get(name, {}).items() if not sc or k.lower() in sc}
        d_both += len(set(g) & set(t)); d_uni += len(set(g) | set(t))
        # AC1 needs the both-ABSENT cell, which Jaccard discards. The universe
        # is the factors this paper could address; a factor neither rater marked
        # is an agreement and Jaccard never credits it.
        universe = sc or {k.lower() for k in set(g) | set(t)}
        ac_by += len(set(g) & set(t))
        ac_go += len(set(g) - set(t))
        ac_ao += len(set(t) - set(g))
        ac_nn += max(0, len(universe) - len(set(g) | set(t)))
        for f in set(g) & set(t):
            ms, ts = spans_for(g[f], sents), spans_for(t[f], sents)
            if ms and ts:
                d_tot += 1; d_hit += bool(ms & ts)
    print(f"\n  per-scope (diagnostic only):  selection {both_f/max(tot_f,1):.3f}  "
          f"same-sentence {agree_s/max(tot_s,1):.3f}")
    print(f"  document level (gated):       selection {d_both/max(d_uni,1):.3f}  "
          f"same-sentence {d_hit/max(d_tot,1):.3f}")

    ac1 = gwet_ac1(ac_by, ac_go, ac_ao, ac_nn)
    print(f"  selection 2x2:  both {ac_by}, gold-only {ac_go}, "
          f"annotator-only {ac_ao}, neither {ac_nn}")

    got = {"agree_selection": d_both / max(d_uni, 1),
           "agree_selection_ac1": ac1,
           "agree_same_sentence": d_hit / max(d_tot, 1),
           "na_rate": na_hits / max(na_total, 1)}
    print()
    bad = []
    for k, (lo, hi) in BANDS.items():
        v = got[k]
        if v != v:            # nan -- AC1 is undefined when nothing varies
            print(f"  ----  {k:22s}  undefined (no variation to correct for)")
            continue
        ok = lo - 1e-9 <= v <= hi + 1e-9
        bad += [] if ok else [k]
        print(f"  {'PASS' if ok else 'FAIL'}  {k:22s} {v:6.3f}   "
              f"band [{lo:.2f}, {hi:.2f}]   real {REAL[k]:.3f}")
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
