"""Extract without a language model, and leave blank what cannot be read.

Produces the same `ExtractionResult` the LLM extractor does, from routes that
were each measured against a null model that reads nothing. No network call, no
API key, no token spend.

## The contract that makes this safe to ship

**A field with no working route is left empty.** `minCount >= 1` in the SHACL
profile is satisfied by a value being PRESENT, not by its being CORRECT, so an
extractor that fills every field produces a package that passes `uofa shacl`
while being mostly wrong. This repository has already paid that bill: 14
turbomachinery models labelled "Class II" validated while packages honestly
writing "Turbomachinery (Centrifugal Pump)" failed, and `wasDerivedFrom` was
satisfied for 27 of 27 packages by the template's own help text.

So the blanks here are the feature. `uofa import` will refuse the package and
name the missing field, which is the correct outcome and the opposite of a silent
pass.

## What it can and cannot fill

| field | route | measured |
|---|---|---|
| `cou_name`, `cou_description` | definitional match | first candidate 0.300; **silence on 7009A 9/10** |
| `model_risk_level` | the standard's own risk table | 5 of 6 real documents |
| model and dataset entities | named-entity patterns | 0.418 / 0.088 vs 0.075 / 0.000 |
| validation results | trained classifier | recall@5 **0.438** vs 0.125 |
| decision outcome | trained classifier | **0.917** balanced, 5 of 6 rejections vs 0 |
| per-factor levels and rationales | — | **left blank**; the best keyless route scores 0.100 end to end |
| requirement entities | — | **left blank**; author-supplied, see below |

**Credibility factor levels are the largest blank and the honest one.** The best
keyless pipeline measured for them reaches 0.100 end to end, so nine in ten
values would be the wrong sentence. Emitting them would fill the template and
corrupt the assessment.

**Requirements are not in a paper.** `bindsRequirement` means the engineering
requirement the model is trusted to help satisfy; that lives in a design history
file or a submission, and only 30% of documents cite a standard at all.

## Confidence is the measured figure

Every `confidence` below is what that route scored on the evaluation corpus, not
a number chosen to look plausible. A field reading 0.088 is telling you it is
usually wrong.
"""
from __future__ import annotations

import re

from uofa_cli.llm_extractor import ExtractionResult, FieldExtraction

# Routes whose numbers are quoted above, so a reader can check one against the
# other without leaving the file.
_CONF = {
    "cou": 0.300,
    "risk": 0.833,
    "model": 0.418,
    "dataset": 0.088,
    "validation": 0.438,
    # Two different claims, two different numbers. "The outcome is Accepted" is
    # the classifier's, measured at 0.917 balanced given the decision sentence.
    # "THIS sentence is the decision" is the locator's, measured at 0.400 top-1.
    # Carrying 0.917 on the quoted span would report one measurement as the
    # other -- the error that had router recall published as an end-to-end
    # result, and it would paint a 40%-likely sentence green in the spreadsheet.
    "decision": 0.917,
    "decision_span": 0.400,
    "files": 1.000,
}

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _sentences(text: str) -> list[str]:
    return [s for s in (t.strip() for t in _SENT.split(text)) if len(s) > 12]


def _fe(value, conf: float, source: str | None = None) -> FieldExtraction:
    return FieldExtraction(value=value, confidence=round(conf, 3),
                           source_file=source)


def _blank(_why: str) -> FieldExtraction:
    """An unfilled field. `_why` documents the call site; the value stays None.

    Deliberately not a placeholder string: a plausible-looking value satisfies
    minCount and turns an honest gap into a validated package.
    """
    return FieldExtraction(value=None, confidence=0.0, source_file=None)


def extract(corpus, pack_name: str) -> ExtractionResult:
    """Keyless extraction over an already-read corpus."""
    from uofa_cli.keyless import routes as R

    text = "\n".join(c.text for c in corpus.chunks)
    sents = _sentences(text)
    pool = list(range(len(sents)))
    src = (corpus.file_manifest[0].get("name")
           if corpus.file_manifest else None)
    is_nasa = "nasa" in pack_name.lower() or "7009" in pack_name

    res = ExtractionResult(model_used="keyless", corpus_tokens=corpus.total_tokens)

    # ── assessment summary ───────────────────────────────────
    summary: dict[str, FieldExtraction] = {}

    # Context of use: NASA-STD-7009A defines no such concept, so silence is the
    # correct answer there and the route is not even consulted.
    if is_nasa:
        summary["cou_name"] = _blank("7009A defines no context of use")
        summary["cou_description"] = _blank("7009A defines no context of use")
    else:
        idx = R.find_context_of_use(sents, pool)
        if idx:
            span = sents[idx[0]]
            summary["cou_name"] = _fe(span[:120], _CONF["cou"], src)
            summary["cou_description"] = _fe(span, _CONF["cou"], src)
        else:
            summary["cou_name"] = _blank("no definitional statement found")
            summary["cou_description"] = _blank("no definitional statement found")

    risk = R.assess(sents, pool)
    if risk.get("derived_risk"):
        summary["model_risk_level"] = _fe(risk["derived_risk"].title(),
                                          _CONF["risk"], src)
    else:
        summary["model_risk_level"] = _blank(
            "model influence x decision consequence not both stated")

    # Left blank on purpose -- each is a judgement, not a string in the document.
    for f in ("project_name", "profile", "device_class", "assurance_level",
              "assessor_name", "has_uq", "standards_reference"):
        summary[f] = _blank("not extractable without judgement")
    res.assessment_summary = summary

    # ── model and data entities ──────────────────────────────
    for kind, etype, conf in (("models", "Model", _CONF["model"]),
                              ("datasets", "Dataset", _CONF["dataset"])):
        for name in R.propose(kind, text, cap=6):
            res.model_and_data.append({
                "entity_type": _fe(etype, conf, src),
                "name": _fe(name, conf, src),
                "description": _blank("no description route"),
            })
    # Requirements are absent by decision, not by failure -- see the module note.

    # ── validation results and the decision ──────────────────
    from uofa_cli.keyless import trained as T
    ok, _why = T.available()
    if ok and sents:
        routes = T.load()
        for span in (routes.validation_results(sents, k=5).value or []):
            res.validation_results.append({
                "name": _fe(span[:120], _CONF["validation"], src),
                "description": _fe(span, _CONF["validation"], src),
                "pass_fail": _blank("not classified"),
                "has_uq": _blank("not classified"),
            })
        d = routes.decision(sents)
        if d.value:
            res.decision = {
                "outcome": _fe(d.value["outcome"], _CONF["decision"], src),
                # The rationale is the top candidate verbatim. Quoting rather
                # than summarising keeps it checkable against the source.
                "rationale": _fe(d.value["candidates"][0],
                                 _CONF["decision_span"], src),
            }
    if not res.decision:
        res.decision = {"outcome": _blank("no trained route available"),
                        "rationale": _blank("no trained route available")}

    # ── credibility factors: named, never scored ─────────────
    # The rows are emitted so the assessment's shape is visible and an author can
    # fill them. Levels and rationales stay empty: the best keyless route for
    # them reaches 0.100 end to end, and a wrong level is worse than a blank one
    # because it validates.
    from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES
    for name in (NASA_ALL_FACTOR_NAMES if is_nasa else VV40_FACTOR_NAMES):
        res.credibility_factors.append({
            # Confidence 0.0, deliberately: the writer paints >= 0.85 green, and
            # these names are not extraction -- they are the standard's own
            # checklist, free and always right. Emitting them at 1.0 made the
            # sheet show 27 green cells for a document where two fields were
            # actually read. That is `control_constant_list` scoring 1.000 on
            # detection, rendered as a colour: enumerating the checklist is not
            # evidence of having assessed it.
            "factor_type": _fe(name, 0.0, None),
            "required_level": _blank("keyless factor scoring is 0.100 end to end"),
            "achieved_level": _blank("keyless factor scoring is 0.100 end to end"),
            "acceptance_criteria": _blank("no route"),
            "rationale": _blank("no route"),
            "status": _fe("not_assessed", 0.0, None),
        })

    res.raw_json = {"keyless": True, "routes": sorted(_CONF),
                    "trained_available": ok, "trained_unavailable_reason": _why}
    return res


def summarise(res: ExtractionResult) -> list[str]:
    """Lines naming what was left blank and why -- printed after every run.

    A run that reports only what it filled reads as a success. The blanks are
    the part a user has to act on, so they are stated rather than inferred from
    an empty cell.
    """
    filled = sum(1 for fe in res.assessment_summary.values() if fe.value is not None)
    blanks = len(res.assessment_summary) - filled
    lines = []
    # A route that could not RUN and a document that contained nothing produce
    # the same "0 results" line, and they mean opposite things. Say which.
    if not res.raw_json.get("trained_available", True):
        lines.append(
            "validation results and the decision were NOT attempted: "
            + res.raw_json.get("trained_unavailable_reason", "route unavailable"))
    return lines + [
        f"{filled} of {len(res.assessment_summary)} summary fields filled, "
        f"{blanks} left blank",
        f"{len(res.credibility_factors)} factors named, "
        f"0 scored — keyless factor scoring is 0.100 end to end",
        "requirements left to the author: the requirement a model is trusted to "
        "help satisfy is not stated in a paper",
    ]
