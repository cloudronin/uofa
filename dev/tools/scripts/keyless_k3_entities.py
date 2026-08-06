#!/usr/bin/env python3
"""K3: find the models, datasets and requirements a document binds.

Three of the thirteen properties `ProfileComplete` requires are entity
bindings, and they are the ones the LLM was worst at -- `bindsRequirement` sat
at 54% under qwen before sonnet took it to 100%. They also have surface form:
model IDs, dataset names and requirement identifiers look like themselves in a
way that "the quantity of interest is relevant to the decision" does not.

## Scored on counts, never on coverage

`control_constant_entity` emits one model called "the model", one dataset and
one requirement. It reads nothing, satisfies `minCount >= 1` on all three
properties, and therefore scores **100% coverage** -- beating the LLM's 82/80/54%
on the metric that was almost shipped.

So coverage cannot judge this. `expected_entities` carries the count of distinct
models, datasets and requirements per bundle, and the constant's answer of "1,
always" is wrong by four on a document naming five models. Mean absolute error
against those counts is the metric, and the constant is the baseline.

## Groundedness cannot see K3's failure mode

A quoted sentence cannot fabricate, which is why K2 scores groundedness 1.000
by construction. K3 has no such immunity: picking the model cited from a
reference paper rather than the one under assessment is a **selection** error.
The wrong answer is still verbatim in the document, so every existing metric
reads it as correct. Counts are what catch it.

## Contamination

Patterns are written from what identifiers look like in general, not from the
corpus. `evidence_keywords` are verbatim source spans and are not consulted.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

# Model identifiers: a NAMED model, not a description of one.
#
# The first version matched "ETW 0.0230" and "ETW 0.095" -- a facility name
# beside a table value -- and "flow solver", "gas model", "alternative solver",
# which are generic phrases every document contains. It reported ~11 models per
# bundle against a ground truth of ~1.8 and lost to a constant answering "1"
# by an MAE of 9.34.
#
# Two changes. The identifier form now requires the digits to be attached
# (CRM-2026, LVAD_v3.4) rather than merely nearby, so a number in an adjacent
# table cell no longer forms an identifier. And the descriptive form requires a
# capitalised proper-noun head, so "SST k-omega model" survives and "flow
# solver" does not.
_MODEL = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9]*[- ]){1,3}(?:[Mm]odel|[Ss]olver|[Ss]imulation|[Cc]ode)\b"
    r"|\b[A-Z]{2,}[A-Z0-9]*[-_](?:v)?\d+(?:\.\d+)*\b"
    r"|\b(?:ANSYS|Abaqus|OpenFOAM|Fluent|STAR-CCM|Nastran|LS-DYNA|OpenSim|COMSOL)"
    r"(?:[- ][A-Za-z0-9.]+)?\b")

# Datasets: named test campaigns, measurement sets, referent data.
_DATASET = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9-]*\s+){0,3}"
    r"(?:dataset|data ?set|test data|measurements?|campaign|rig data|"
    r"benchmark|corpus|test series|experimental data)\b", re.I)

# Requirements: identifiers, or a sentence stating one.
_REQUIREMENT = re.compile(
    r"\b(?:REQ|SR|SYS|FR|PR)[-_ ]?\d+(?:\.\d+)*\b"
    r"|\brequirement\s+[A-Z0-9][-A-Za-z0-9.]*\b"
    r"|\bshall\s+(?:not\s+)?[a-z]", re.I)

# Generic heads: present in every document, name nothing.
_GENERIC = ("flow", "gas", "alternative", "epistemic", "cross-code", "the",
            "this", "a", "our", "each", "both", "other", "same", "full",
            "baseline", "production", "current", "reference", "candidate")
_STOP = {"the model", "this model", "a model", "the models", "our model",
         "the simulation", "the code", "the solver", "the dataset", "the data"}


def _uniq(matches, cap: int = 40) -> set[str]:
    out = set()
    for m in matches:
        s = " ".join(m.split()).strip(" .,:;()")
        low = s.lower()
        if len(s) < 3 or low in _STOP:
            continue
        if low.split()[0] in _GENERIC:
            continue
        out.add(s.lower())
        if len(out) >= cap:
            break
    return out


def extract_entities(text: str) -> dict[str, int]:
    """Distinct model / dataset / requirement mentions."""
    return {
        "models": len(_uniq(_MODEL.findall(text))),
        "datasets": len(_uniq(_DATASET.findall(text))),
        "requirements": len(_uniq(_REQUIREMENT.findall(text))),
    }


# Sections whose contents are citations rather than subjects. A model named
# only under "References" is somebody else's.
_CITATION_SECTION = re.compile(
    r"^\s*#{1,6}\s*(references|bibliography|prior work|related work|"
    r"further reading|appendix [a-z]?\s*[-:]?\s*references)\b", re.I | re.M)


def _strip_citation_sections(text: str) -> str:
    """Drop everything from a references heading to the next heading."""
    out, pos = [], 0
    for m in _CITATION_SECTION.finditer(text):
        out.append(text[pos:m.start()])
        nxt = re.search(r"^\s*#{1,6}\s+\S", text[m.end():], re.M)
        pos = m.end() + (nxt.start() if nxt else len(text) - m.end())
    out.append(text[pos:])
    return "".join(out)


def extract_entities_salient(text: str) -> dict[str, int]:
    """K3b: count only entities that behave like the document's SUBJECT.

    K3 failed by over-counting: ~5 models per bundle against a ground truth of
    ~1.8, losing to a constant that answers "1". The cause is not typing --
    every match really is a model name -- it is *role*. A document names the
    model under assessment, the solver it runs on, models it is compared
    against, and models cited from the literature, and all four look identical
    to a pattern and to an off-the-shelf NER. Measured: spaCy tags the real
    identifier AERO-CRM-2026 as LAW and returns 58 distinct ORGs against a
    ground truth of 4 models.

    Salience is the signal a type system does not carry:

    * an entity named in the opening (title, abstract, scope) is the subject
    * an entity named only under References is someone else's
    * the subject recurs; a passing mention appears once

    None of this needs new supervision, which matters because
    `expected_entities` carries counts and not spans, so there is nothing to
    train a span model on even if typing were the problem.
    """
    body = _strip_citation_sections(text)
    head = body[:1500]                       # title, abstract, scope
    low_body = body.lower()

    out = {}
    for kind, rx in (("models", _MODEL), ("datasets", _DATASET),
                     ("requirements", _REQUIREMENT)):
        cands = _uniq(rx.findall(body))
        keep = set()
        for c in cands:
            in_head = c in head.lower()
            recurs = low_body.count(c) >= 2
            if in_head or recurs:
                keep.add(c)
        # Requirements are enumerated rather than discussed, so recurrence is
        # the wrong test for them: REQ-4.2 legitimately appears once.
        out[kind] = len(cands) if kind == "requirements" else len(keep)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.glob("bundle_*"))
               if (b / "ground_truth.json").exists() and (b / "source").is_dir()]
    kinds = ("models", "datasets", "requirements")
    err = {k: [] for k in kinds}
    err_sal = {k: [] for k in kinds}
    err_const = {k: [] for k in kinds}
    n = 0

    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        want = gt.get("expected_entities") or {}
        if not want:
            continue
        n += 1
        src = "\n".join(p.read_text(errors="ignore")
                        for p in sorted((b / "source").glob("*")))
        got = extract_entities(src)
        got_s = extract_entities_salient(src)
        for k in kinds:
            w = want.get(k)
            if not isinstance(w, int):
                continue
            err[k].append(abs(got[k] - w))
            err_sal[k].append(abs(got_s[k] - w))
            err_const[k].append(abs(1 - w))      # the constant always says 1

    print(f"\nK3 — entity patterns   ({n} bundles)\n")
    print(f"  {'property':16s} {'K3 MAE':>8s} {'K3b MAE':>9s} {'const':>8s} {'K3b-const':>10s}")
    passes = 0
    for k in kinds:
        if not err[k]:
            continue
        a = statistics.mean(err[k])
        s = statistics.mean(err_sal[k])
        c = statistics.mean(err_const[k])
        better = c - s
        passes += better > 0
        print(f"  {k:16s} {a:>8.2f} {s:>9.2f} {c:>8.2f} {better:>+10.2f}")

    print(f"\n  KILL CRITERION: beat control_constant_entity on count MAE (K3b)")
    print(f"  -> {'PASSES' if passes >= 2 else 'FAILS'} ({passes}/3 properties better)")
    print(f"\n  Coverage is not reported here on purpose: the constant satisfies")
    print(f"  minCount on all three and scores 100%, beating the LLM's 82/80/54%.")
    print(f"  Counts are the only thing that separates reading from asserting.")
    print(f"\n  Synthetic only — real-document transfer unverified (V1 deferred).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
