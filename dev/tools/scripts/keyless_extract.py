#!/usr/bin/env python3
"""Extract a credibility package without a model, and refuse to invent the rest.

`UnitOfAssurance_CompleteBody` requires thirteen properties at `minCount >= 1`,
nine of them from the extractor. Two keyless routes work, four are weak, three
fail. This walks that table, records which route produced each value, and
**emits nothing where no route works**.

The shape is an `sh:or` over three profiles -- Minimal (7 properties), Complete
(13), Disposition (14) -- so a sparse package does not fail for want of one
field, it fails to reach any profile. Keyless supplies **one of Minimal's seven**
(`hasContextOfUse`); three more of the seven are exactly the properties with no
keyless route, and the last three come from signing. So no amount of tuning makes
a keyless-only package validate: the gap is structural, not a matter of accuracy.

## Why absence is the whole design

`minCount >= 1` requires a property to be PRESENT, not CORRECT. An extractor that
emits something for all thirteen produces a package that passes `uofa shacl`
while being mostly wrong, and this project has already paid for that:

* 14 turbomachinery models labelled "Class II" validated, while packages honestly
  writing "Turbomachinery (Centrifugal Pump)" failed -- the constraint rewarded
  fabrication and punished accuracy
* `wasDerivedFrom` was satisfied for 27 of 27 packages by the template's own help
  text, "DOI, report number, or URI"
* 37 of 45 packages failed the shape while the eval reported `mean overall F1
  0.964 -- PASS`

So a property with no keyless route is emitted as `null` with
`method: "no-keyless-route"`, and validation fails loudly with a precise reason.
A package that cannot be honestly filled should not validate, and a keyless
extractor whose selling point is "no API key" must not buy that with fabrication.

## Provenance on every value

Each property carries `method`, `confidence` and the verbatim span it came from,
so a reader can ask which parts of a package were pattern-matched and which
needed judgement. That question is currently unanswerable about any package this
tool has ever produced.

## Confidence is measured, not asserted

Every `confidence` here is the end-to-end figure that route scored on the seeded
corpus, not a number chosen to look reasonable. `hasCredibilityFactor` reports
0.100 because that is what k6+k10 achieves, and a reader who sees 0.100 and does
not trust the value is reading it correctly.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import keyless_k3c_named_entities as K3c  # noqa: E402
import keyless_k7_context_of_use as K7  # noqa: E402
import keyless_k8_model_risk as K8  # noqa: E402
from keyless_k5_sections import extract_decision  # noqa: E402
from keyless_pipeline_registry import Doc, read  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402

# Measured end-to-end on the seeded corpus. Not chosen.
#   works      -- beats every control, and by a margin worth acting on
#   weak       -- beats its control, too low to rely on
#   no-route   -- loses to a control, or is not demonstrated
#
# `hasContextOfUse` carries 0.300, not K7's published 0.750, for two reasons and
# both are worth stating. The 0.750 was measured on a train split regenerated
# three times afterwards -- rerun today K7 is 9/20 and its control is also 9/20.
# And K7's figure scores a hit if ANY of its top three candidates is right, while
# an extractor emits ONE value; first-candidate accuracy is 0.300. Composing a
# published number measured under different conditions is how router recall came
# to be reported as an end-to-end result.
ROUTES = {
    "modelRiskLevel":       ("k8",  "works",    0.833),   # 5 of 6 documents
    "hasContextOfUse":      ("k7",  "weak",     0.300),   # first candidate, train
    "prov:wasDerivedFrom":  ("files", "works",  1.000),   # a run fact, not extraction
    "hasCredibilityFactor": ("k6+k10", "weak",  0.100),   # end-to-end sweep best
    "bindsModel":           ("k3c", "weak",     0.418),
    "bindsDataset":         ("k3c", "weak",     0.088),
    "bindsRequirement":     (None,  "no-route", 0.0),     # 0.026 < a naive 0.039
    "hasValidationResult":  (None,  "no-route", 0.0),     # p = 0.094, not demonstrated
    "hasDecisionRecord":    (None,  "no-route", 0.0),     # 0.033 against a 0.833 control
}
# Supplied by signing and import, never by an extractor.
OUT_OF_SCOPE = ("uofa:hash", "uofa:signature", "prov:generatedAtTime",
                "prov:wasAttributedTo")


def required_properties() -> list[str]:
    """The 13, read from the shape rather than typed here.

    A hand-kept copy of this list is a list that drifts, and the first draft of
    this file proved it: `hasCredibilityFactor` was declared in ROUTES, never
    emitted, and nothing noticed -- the exact defect the tool exists to catch,
    in the tool. `PROFILE_URIS` was moved off a literal onto `sh:in` for the
    same reason.
    """
    from rdflib import RDF, Graph, Namespace
    SH = Namespace("http://www.w3.org/ns/shacl#")
    g = Graph().parse(_ROOT / "packs" / "core" / "shapes" / "uofa_shacl.ttl",
                      format="turtle")
    shape = next(s for s in g.subjects(RDF.type, SH.NodeShape)
                 if "UnitOfAssurance_CompleteBody" in str(s))
    out = []
    for p in g.objects(shape, SH.property):
        mc = g.value(p, SH.minCount)
        if mc is not None and int(mc) >= 1:
            out.append(g.qname(g.value(p, SH.path)))
    return sorted(out)


def _val(value, method: str, confidence: float, span: str | None = None) -> dict:
    return {"value": value, "method": method, "confidence": round(confidence, 3),
            "span": span}


def _absent(reason: str) -> dict:
    """A property with no keyless route. Never a plausible-looking placeholder."""
    return {"value": None, "method": "no-keyless-route", "confidence": 0.0,
            "span": None, "reason": reason}


def extract(doc: Doc, standard: str = "V&V40", ctx=None) -> dict:
    """A package body, with provenance, and holes where the holes are.

    `ctx` carries the sweep's classifier and encoder. Without it the credibility
    factors are absent for want of a router, which is a different absence from
    "no keyless route exists" and is labelled differently.
    """
    text = "\n".join(doc.texts)
    out: dict[str, dict] = {}

    # modelRiskLevel -- K8 derives it from the standard's own table, and returns
    # not_derivable rather than guessing when an input is renamed or undefined.
    #
    # K8 is an AUDIT tool: `not_derivable` covers both "the two inputs are
    # missing" and "they are present, but the paper states no risk to compare
    # the derivation against". Only the first is an extraction failure. Gating
    # on `agreement` discarded a derived risk on a document where the table had
    # done its job, because nothing was there to disagree with it.
    risk = K8.assess(doc.sents, doc.pool)
    if not risk.get("derived_risk"):
        out["uofa:modelRiskLevel"] = _absent(
            "K8: model influence x decision consequence not stated"
            + (f"; substituted term {risk['substituted_term']!r}"
               if risk.get("substituted_term") else ""))
    else:
        out["uofa:modelRiskLevel"] = _val(
            risk["derived_risk"], "k8", ROUTES["modelRiskLevel"][2],
            risk.get("stated_risk"))
        # A derived risk contradicting the stated one is the finding K8 exists
        # to surface, so it travels with the value rather than being resolved.
        if risk.get("agreement") == "mismatch":
            out["uofa:modelRiskLevel"]["disagrees_with_stated"] = risk["stated_risk"]

    # hasContextOfUse -- V&V 40 only. R9: 7009A has no such concept, and any
    # value on such a document is invented.
    if standard != "V&V40":
        out["uofa:hasContextOfUse"] = _absent(
            "NASA-STD-7009A defines no context of use; a value here would be "
            "fabricated")
    else:
        idx = K7.find_context_of_use(doc.sents, doc.pool)
        out["uofa:hasContextOfUse"] = (
            _val(doc.sents[idx[0]].strip(), "k7", ROUTES["hasContextOfUse"][2],
                 doc.sents[idx[0]].strip())
            if idx else _absent("K7 found no definitional statement"))

    # bindsModel / bindsDataset -- named entities. Weak, and labelled weak.
    for prop, kind in (("uofa:bindsModel", "models"),
                       ("uofa:bindsDataset", "datasets")):
        names = K3c.propose(kind, text, cap=6)
        conf = ROUTES[prop.split(":")[1]][2]
        out[prop] = (_val(names, "k3c", conf, None) if names
                     else _absent(f"K3c proposed no {kind}"))

    # The three with no keyless route. Each names the measurement that says so.
    out["uofa:bindsRequirement"] = _absent(
        "K3c scores 0.026 on requirement names, below a naive baseline's 0.039")
    out["uofa:hasValidationResult"] = _absent(
        "K9 scores 18/100 against a control's 13/100, p = 0.094 -- not demonstrated")
    dec, _src = extract_decision(text)
    out["uofa:hasDecisionRecord"] = _absent(
        "K5 scores 0.033 against a 0.833 constant"
        + (f"; a section scan saw {dec!r}, which is recorded here and not emitted"
           if dec else ""))

    # hasCredibilityFactor -- the sweep's winner, k6 routing into k10 selection.
    # 0.100 end to end is what it scores, and the value carries that figure so a
    # reader distrusting it is reading it correctly. Nine in ten of these spans
    # are the wrong sentence.
    if ctx is None:
        out["uofa:hasCredibilityFactor"] = _absent(
            "no router loaded; run with --factors to build the classifier")
    else:
        found = []
        for factor in sorted(ec.VV40_FACTOR_NAMES if standard == "V&V40"
                             else ec.NASA_ALL_FACTOR_NAMES):
            shortlist, chosen = ctx.pipe.run(doc, factor, ctx, 5)
            if shortlist and chosen >= 0:
                found.append({"factor": factor,
                              "span": doc.texts[shortlist[chosen]].strip()})
        out["uofa:hasCredibilityFactor"] = (
            _val(found, "k6+k10", ROUTES["hasCredibilityFactor"][2], None)
            if found else _absent("k6 ranked no sentence for any factor"))

    out["prov:wasDerivedFrom"] = _val(
        [p.name for p in sorted((doc.bundle / "source").glob("*"))],
        "files", 1.000, None)

    for p in OUT_OF_SCOPE:
        out[p] = _absent("supplied by signing or import, not by an extractor")
    return out


def judge(pkg: dict, gt: dict) -> dict[str, bool]:
    """Was each emitted value RIGHT. Only scores properties the gold covers.

    Fill rate is presence, and presence is the thing this file argues is not the
    measure. A table of fill rates would repeat the mistake it was written to
    prevent -- so anything filled is checked against the gold, and anything the
    gold does not cover is left out of the table rather than counted as correct.
    """
    got: dict[str, bool] = {}

    for prop, kind in (("uofa:bindsModel", "models"),
                       ("uofa:bindsDataset", "datasets")):
        want = (gt.get("expected_entity_names") or {}).get(kind) or []
        have = pkg.get(prop, {}).get("value") or []
        if want:
            got[prop] = any(K3c.names_match(h, w) for h in have for w in want)

    want_cou = gt.get("expected_context_of_use")
    have_cou = pkg.get("uofa:hasContextOfUse", {}).get("value")
    if want_cou:
        got["uofa:hasContextOfUse"] = bool(
            have_cou and _overlaps(have_cou, want_cou))

    # A factor is right if the selected span is one the annotator marked for it.
    gold: dict[str, list[str]] = {}
    for f in gt.get("findings", []):
        if f.get("status") == "ambiguous":
            continue
        for s in (f.get("spans") or [f["span"]]):
            gold.setdefault(f["factor"], []).append(" ".join(s.split()).lower())
    have = pkg.get("uofa:hasCredibilityFactor", {}).get("value") or []
    scored = [(" ".join(e["span"].split()).lower(), gold.get(e["factor"], []))
              for e in have if e["factor"] in gold]
    if scored:
        got["uofa:hasCredibilityFactor"] = None       # per-span, tallied below
        got["_factors"] = sum(any(g in s for g in gs) for s, gs in scored)
        got["_factors_n"] = len(scored)
    return got


def _overlaps(a: str, b: str, need: float = 0.5) -> bool:
    """Content-word overlap, the same test K7 is scored with."""
    wa = {w for w in a.lower().split() if len(w) > 3}
    wb = {w for w in b.lower().split() if len(w) > 3}
    return bool(wb) and len(wa & wb) / len(wb) >= need


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", type=pathlib.Path, default=None)
    ap.add_argument("--factors", action="store_true",
                    help="load the k6 classifier and route credibility factors "
                         "(slow; without it that property is absent for want of "
                         "a router, not for want of a route)")
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
               if (b / "source").is_dir()]
    if args.limit:
        bundles = bundles[:args.limit]

    ctx = None
    if args.factors:
        from keyless_pipeline_registry import Pipeline
        from keyless_sweep import Ctx
        ctx = Ctx()
        ctx.pipe = Pipeline(route="k6", select="k10")   # the sweep's winner

    filled = absent = 0
    per_prop: dict[str, int] = {}
    right: dict[str, int] = {}
    judged: dict[str, int] = {}
    fac: dict[str, int] = {}
    packages = {}
    for b in bundles:
        doc = read(b)
        gt = (json.loads((b / "ground_truth.json").read_text())
              if (b / "ground_truth.json").exists() else {})
        pkg = extract(doc, gt.get("standard", "V&V40"), ctx)
        packages[b.name] = pkg
        missing = [p for p in required_properties() if p not in pkg]
        if missing:
            raise SystemExit(
                f"{b.name}: {len(missing)} required properties absent from the "
                f"output entirely: {missing}. A property the extractor does not "
                f"mention is indistinguishable from one it decided to skip, and "
                f"this is how `hasCredibilityFactor` went missing while being "
                f"listed as routed.")
        for prop, v in pkg.items():
            if prop in OUT_OF_SCOPE:
                continue
            if v["value"] in (None, [], ""):
                absent += 1
            else:
                filled += 1
                per_prop[prop] = per_prop.get(prop, 0) + 1

        for prop, ok in judge(pkg, gt).items():
            if prop.startswith("_"):
                fac[prop] = fac.get(prop, 0) + ok
            elif ok is not None:
                right[prop] = right.get(prop, 0) + ok
                judged[prop] = judged.get(prop, 0) + 1

    n = len(bundles)
    print(f"\nKeyless extract — {n} documents\n")
    print(f"  {'property':28s}{'filled':>8s}{'method':>10s}{'confidence':>12s}"
          f"{'CORRECT':>12s}")
    order = ["uofa:modelRiskLevel", "uofa:hasContextOfUse",
             "uofa:hasCredibilityFactor", "uofa:bindsModel", "uofa:bindsDataset",
             "prov:wasDerivedFrom", "uofa:bindsRequirement",
             "uofa:hasValidationResult", "uofa:hasDecisionRecord"]
    for prop in order:
        # Look up by the full name first: ROUTES keys prov: properties with
        # their prefix, and stripping it silently reported wasDerivedFrom as
        # having no route while it was filling 10 of 10.
        method, _grade, conf = ROUTES.get(
            prop, ROUTES.get(prop.split(":")[1], (None, "no-route", 0.0)))
        got = per_prop.get(prop, 0)
        if prop == "uofa:hasCredibilityFactor" and fac.get("_factors_n"):
            acc = f"{fac['_factors'] / fac['_factors_n']:.3f}"
        elif judged.get(prop):
            acc = f"{right.get(prop, 0) / judged[prop]:.3f}"
        else:
            acc = "no gold"
        print(f"  {prop:28s}{got:>4d}/{n:<3d}{str(method or '—'):>10s}"
              f"{conf:>12.3f}{acc:>12s}")

    print(f"\n  values emitted {filled}, honestly absent {absent}")
    print("\n  'filled' is presence and 'CORRECT' is accuracy against the gold,")
    print("  measured only where the gold covers the property. They are different")
    print("  numbers and the second is the one that matters: minCount is satisfied")
    print("  by the first.")
    print("\n  Every absence above is a property no keyless route extracts. Filling")
    print("  them would make these packages pass `uofa shacl`, because minCount")
    print("  requires presence and not correctness -- which is how 14 turbomachinery")
    print("  models came to be labelled 'Class II' and validate.")
    if args.json:
        args.json.write_text(json.dumps(packages, indent=2) + "\n")
        print(f"\n  wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
