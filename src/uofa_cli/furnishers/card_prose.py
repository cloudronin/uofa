"""Extract a model card's REPORTED evaluation results as ValidationResult nodes.

The second Group-B furnisher. raidex furnishes measurements; this furnishes what
the card's own authors published about their model. Both are assessed by the same
rules, and `evidenceSource` keeps them distinguishable -- a self-reported score
and an independent measurement are different claims about the same subject.

**Backend-required, unlike the raidex adapter.** Reading a structured record is a
field read and infers nothing; reading prose is inference, and the pack spec's §4
split turns on exactly that. There is no heuristic fallback here: a keyless run
reports that evaluation is present and unassessed rather than guessing at it.

**Only sliced text is sent.** The caller passes `card_eval.scoped_text(...)`, so
the model never sees "How to use" and cannot contribute a temperature from it.
That guarantee is structural and lives in `card_eval`; this module must not
undo it by falling back to the full card when the slice is empty.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from uofa_cli import paths
from uofa_cli.excel_mapper import slugify

EVIDENCE_SOURCE = "reported"

# Values a model emits when it means "absent". Every one of them must become an
# OMITTED property, never a present one. A node carrying `nullBaselineStatement:
# "not reported"` satisfies the rule's noValue() check and silences
# W-EV-NULL-04 -- reporting a gap as though it were filled, which is the failure
# the whole Group-B layer exists to catch. Same discipline as the raidex
# adapter's "N/A"-string rule, arriving by a different route.
_SENTINELS = frozenset({
    "", "-", "--", "n/a", "na", "none", "null", "nil", "unknown", "unspecified",
    "not reported", "not stated", "not specified", "not available", "not given",
    "no", "not applicable", "tbd", "?",
})

# The prompt asks for `=== SECTION ===`. Models routinely emit the bare header
# instead -- Llama-3.3-70B does it on every response -- and a parser that
# accepts only the delimited form returns ZERO nodes for a well-formed
# extraction. Measured: 116/116 cases scored as "reports nothing" while the
# model was correctly reading uncertainties and seed counts.
#
# The section names are a closed set, so matching a bare header line is
# unambiguous; this is not loosening the format, it is not mistaking
# punctuation for content.
_SECTION_NAMES = ("VALIDATION_RESULT", "EXTRACTION_NOTES")
_BLOCK = re.compile(
    r"^(?:===\s*(?P<delim>[A-Z_]+)\s*===|(?P<bare>"
    + "|".join(_SECTION_NAMES) + r"))\s*:?\s*$", re.M)
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


@dataclass(frozen=True)
class ReportedEvidence:
    """Reported results parsed from a card, plus what could not be resolved."""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)
    # Non-empty when the response carried extractable content the parser could
    # not read. Distinct from "no nodes": an empty extraction is a claim that the
    # card reports nothing, and a parse failure must never be able to make that
    # claim on the card's behalf.
    parse_error: str = ""


DEFAULT_MAX_TOKENS = 16384


def extract(scoped_text: str, base: str, *, model: str | None = None,
            llm_config=None, source_url: str = "", subject_revision: str = "",
            pack: str = "model-credibility",
            max_tokens: int = DEFAULT_MAX_TOKENS) -> "ReportedEvidence":
    """Run the prose extractor over a card's scoped evaluation sections.

    The missing join. This module has carried a prompt and a parser since Phase
    4 with nothing between them, so `card_prose` had no production caller and the
    Group-B prose path never actually ran.

    Backend-required by design (D2): prose is where a plausible inferred value
    could pass as a read one, which is exactly what a backend must be accountable
    for. Structured furnisher input reads deterministically and does not come
    through here.

    `{corpus}` is substituted rather than `.format()`-ed -- the prompt contains
    literal braces in its field examples, and `.format()` would raise on them or,
    worse, silently consume one.
    """
    from uofa_cli.llm import GenerationOptions, get_backend

    prompt = prompt_path(pack).read_text(encoding="utf-8").replace(
        "{corpus}", scoped_text)

    config = llm_config
    if config is None:
        from uofa_cli.llm_extractor import _legacy_model_to_config
        config = _legacy_model_to_config(model or "")

    response = get_backend(config).generate(prompt, GenerationOptions(
        timeout_seconds=600.0,
        # An eval section yields a handful of blocks, so 4096 is ample for a
        # plain instruct model -- but a REASONING model spends this budget
        # before it emits any visible content, and runs out mid-thought. Pinned
        # in the result because a cap that truncates is part of the
        # configuration a number belongs to.
        max_tokens=max_tokens,
        # Determinism where the backend honours it: this path feeds a
        # measurement, and a specificity number computed against a moving
        # extractor is not a measurement of anything.
        temperature=0.0,
        seed=20260811,
        extra={"think": False},
    ))
    return parse(response, base, source_url, subject_revision)


def prompt_path(pack: str = "model-credibility") -> Path:
    return paths.pack_dir(pack) / "prompts" / "card_eval_extract_prompt.txt"


def _clean(value: str | None) -> str:
    """A stated value, or "" when the text stated nothing.

    Sentinel-stripping happens here, once, so no caller has to remember it. The
    check is on the whole trimmed value: a genuine statement that merely contains
    the word "none" ("none of the runs used sampling") is kept.
    """
    if value is None:
        return ""
    text = value.strip().strip("`*_").strip()
    return "" if text.lower() in _SENTINELS else text


def _blocks(response: str) -> list[tuple[str, dict[str, str]]]:
    """Parse `=== SECTION ===` kv-blocks, preserving order and duplicates."""
    out: list[tuple[str, dict[str, str]]] = []
    text = response or ""
    # Two capture groups per match (delimited, bare), so split yields
    # [preamble, delim, bare, body, delim, bare, body, ...].
    parts = _BLOCK.split(text)
    for delim, bare, body in zip(parts[1::3], parts[2::3], parts[3::3]):
        name = delim or bare
        fields: dict[str, str] = {}
        key = None
        for line in body.splitlines():
            match = re.match(r"^([a-z_]+):\s*(.*)$", line.strip())
            if match:
                key = match.group(1)
                fields[key] = match.group(2)
            elif key and line.strip():           # continuation of a wrapped value
                fields[key] = (fields[key] + " " + line.strip()).strip()
        out.append((name, fields))
    return out


def _numeric(value: str) -> float | None:
    match = _NUMBER.search(value or "")
    return float(match.group(0)) if match else None


_FIELD_LINE = re.compile(
    r"^\s*(?:name|metric_value|metric_name|uncertainty|null_baseline|"
    r"harness_determinism|sampling_account|confound_control|claimed_cou)\s*:",
    re.M)


def _unparsed(response: str, blocks: list) -> str:
    """Did the response clearly carry blocks the parser failed to read?

    Zero nodes is a legitimate outcome -- a card may genuinely report nothing.
    Zero nodes from a response full of `metric_value:` lines is a PARSER
    failure wearing that outcome's clothes, and it is indistinguishable from the
    real thing at every downstream point. Measured cost of not checking: an
    extractor scored 0/116 on content it had read correctly.
    """
    if blocks:
        return ""
    if not (response or "").strip():
        # Third instance of this class today. An empty completion is a FAILED
        # CALL, and scoring it as "the card reports nothing" credits the
        # extractor with a correct silence on every absent case and blames it
        # for a miss on every present one -- from the same non-event.
        # Measured: Qwen3.5-9B on Together routes all output to a `reasoning`
        # field and returns content='', finish_reason='length'. 116 empty
        # responses were being scored as absences.
        return "empty response from the backend; not an extraction"
    hits = len(_FIELD_LINE.findall(response or ""))
    if hits >= 2:
        return (f"response carried {hits} extractor field lines but no parseable "
                f"block header; refusing to report this as an empty extraction")
    return ""


def parse(response: str, base: str, source_url: str = "",
          subject_revision: str = "") -> ReportedEvidence:
    """Turn an extractor response into ValidationResult nodes.

    A block with no usable score is SKIPPED rather than emitted with a null one.
    A node asserting "reported, value unknown" is a fabricated reading of the
    card: the card either states a number or it does not.

    `subject_revision` is the pinned revision of the artifact the scores describe
    -- for an open-weight HF model, the repo revision, which pins the weights and
    not merely the card text. Supplying it sets `subjectVersionGuarantee` and
    silences W-EV-SUB-08 for these nodes, correctly: that rule's grounding is
    configuration control, and a model retrievable at an immutable revision IS
    configuration-controlled. Firing there was a false finding by the rule's own
    doctrine, the same class as W-EP-02 reporting "no provenance" on evidence
    that had provenance.

    Leave it empty when the subject cannot be pinned, and the rule fires as it
    does for API-hosted subjects.
    """
    nodes: list[dict[str, Any]] = []
    notes: list[str] = []
    skipped: list[dict[str, str]] = []
    seen: set[str] = set()

    parsed = _blocks(response)
    for name, fields in parsed:
        if name == "EXTRACTION_NOTES":
            note = _clean(fields.get("notes"))
            if note:
                notes.append(note)
            continue
        if name != "VALIDATION_RESULT":
            continue

        benchmark = _clean(fields.get("name"))
        score = _numeric(_clean(fields.get("metric_value")))
        if not benchmark:
            skipped.append({"reason": "no benchmark name", "block": str(fields)[:120]})
            continue
        if score is None:
            skipped.append({"benchmark": benchmark, "reason": "no numeric score stated"})
            continue

        slug = slugify(benchmark)
        if slug in seen:                          # same benchmark twice: keep the first
            skipped.append({"benchmark": benchmark, "reason": "duplicate block"})
            continue
        seen.add(slug)

        node: dict[str, Any] = {
            "id": f"{base}/validation/reported-{slug}",
            "type": "ValidationResult",
            "name": benchmark,
            "metricValue": score,
            "evidenceSource": EVIDENCE_SOURCE,
        }
        if subject_revision:
            node["subjectVersionGuarantee"] = str(subject_revision)
        shots = _clean(fields.get("shot_count"))
        metric = _clean(fields.get("metric_name"))
        descriptor = ", ".join(p for p in (metric, shots) if p)
        node["description"] = (f"{benchmark} reported in the model card"
                               + (f" ({descriptor})" if descriptor else ""))

        # Optional properties: present ONLY when the card stated them. Each maps
        # to a rule that fires on its absence, so emitting a placeholder here
        # would silence that rule on evidence the card never provided.
        for field_name, prop in (
            ("uncertainty", "hasUncertaintyQuantification"),
            ("null_baseline", "nullBaselineStatement"),
            ("harness_determinism", "harnessDeterminismStatement"),
            ("sampling_account", "samplingAccount"),
            ("confound_control", "confoundControlStatement"),
            ("claimed_cou", "claimedCOU"),
        ):
            stated = _clean(fields.get(field_name))
            if stated:
                node[prop] = stated
        if "hasUncertaintyQuantification" in node:
            node["uqMethod"] = f"as reported in the model card: {node['hasUncertaintyQuantification']}"
            node["hasUncertaintyQuantification"] = True

        node["wasGeneratedBy"] = {
            "id": f"{node['id']}/activity",
            "type": "prov:Activity",
            "activityType": "model-card-reported-evaluation",
            "description": ("Reported by the model card's authors"
                            + (f"; source {source_url}" if source_url else "")),
        }
        nodes.append(node)

    return ReportedEvidence(nodes=nodes, notes=notes, skipped=skipped,
                            parse_error=_unparsed(response, parsed))


# ── W-EV-DIV-07: matching a reported score to a furnished one ───────────────

DIV_TOLERANCE_NORMALIZED = 5.0
"""Divergence tolerance on the 0-100 scale, used when the furnished result
carries no uncertainty of its own.

Measured, not chosen. Across all 43 published raidex records (427 results),
`bbq` is the only constituent publishing a standard error, and those span
1.84 to 4.08 points normalised (`studies/cohort-2026-08`). A tolerance at or
below 4.08 would fire on sampling noise at the furnisher's own sample sizes,
so 5.0 sits just above the cohort maximum.

The fixed form is the dominant path, not a fallback: a rule that fired only
where uncertainty exists would go silent on 8 of 9 constituents -- precisely
where the evidence is weakest, which inverts the point of having the rule.
"""


def _alias_map(pack: str = "model-credibility") -> dict[str, str]:
    import json
    path = paths.pack_dir(pack) / "data" / "constituent_aliases.json"
    return json.loads(path.read_text(encoding="utf-8"))["aliases"]


def _constituent_of(name: str, aliases: dict[str, str]) -> str | None:
    """The furnisher constituent a reported benchmark name refers to, or None.

    Exact normalised match only. Fuzzy matching would let "MMLU" reach "wmdp" by
    edit distance and manufacture a divergence between unrelated measurements --
    a finding indistinguishable, to a reader, from the one that matters. An
    unmatched name yields None and no comparison happens.
    """
    key = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    return aliases.get(key)


def match_and_compare(reported: list[dict[str, Any]], furnished: list[dict[str, Any]],
                      pack: str = "model-credibility") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Link reported results to furnished ones measuring the same constituent.

    Returns (annotated_reported, comparisons). A reported node gains
    `corroboratedBy` when a furnished counterpart exists -- which is what
    retires W-EV-COR-09 on that node -- and a comparison record is produced so
    W-EV-DIV-07 can be evaluated on the delta.

    Mutates nothing: callers get new dicts, so a failed match cannot leave half
    of one applied.
    """
    aliases = _alias_map(pack)
    by_constituent: dict[str, dict[str, Any]] = {}
    for node in furnished:
        slug = str(node.get("id", "")).rsplit("-", 1)[-1]
        if slug:
            by_constituent.setdefault(slug, node)

    annotated: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for node in reported:
        constituent = _constituent_of(node.get("name", ""), aliases)
        counterpart = by_constituent.get(constituent) if constituent else None
        if counterpart is None:
            annotated.append(dict(node))
            continue

        linked = dict(node, corroboratedBy=counterpart["id"])
        reported_value = node.get("metricValue")
        furnished_value = counterpart.get("metricValue")
        if isinstance(reported_value, (int, float)) and isinstance(furnished_value, (int, float)):
            delta = abs(float(reported_value) - float(furnished_value))
            # The furnished side's own uncertainty when it has one, else the
            # measured cohort tolerance.
            tolerance = DIV_TOLERANCE_NORMALIZED
            basis = "cohort tolerance"
            stated = counterpart.get("uqMethod") or ""
            found = _NUMBER.search(stated.split("standard error", 1)[-1]) if "standard error" in stated else None
            if found:
                tolerance = float(found.group(0)) * 100.0 if float(found.group(0)) < 1 else float(found.group(0))
                basis = "furnished uncertainty"
            comparisons.append({
                "constituent": constituent,
                "reported": float(reported_value),
                "furnished": float(furnished_value),
                "delta": round(delta, 3),
                "tolerance": round(tolerance, 3),
                "basis": basis,
                "diverges": delta > tolerance,
                "reportedNode": node["id"],
                "furnishedNode": counterpart["id"],
            })
            if delta > tolerance:
                linked["divergesFromFurnished"] = round(delta, 3)
        annotated.append(linked)
    return annotated, comparisons
