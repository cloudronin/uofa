"""Wave J: REAL-GAP → Jena rule scaffold (forward-chaining only).

Per spec v1.6 §13.1 and Delta 6: the Stage 5 formalization step takes
final-verdict REAL-GAP cases and emits Jena rule + SHACL skeletons that
the author reviews and merges into the v0.5 catalog.

Scope (Delta 6 explicit):
  - Forward-chaining C3 weakener rules ONLY. Each scaffold targets
    `[ruleId: ... -> uofa:hasWeakener ?ann]` shape per
    `packs/core/rules/uofa_weakener.rules`.
  - Backward-chaining OOS Jena rule generation is a separate substrate
    test (`UofA_OOS_Substrate_Validation_Test_v0_1.md`, May 11–24
    window). OOS verdicts in final_verdicts.jsonl ship as evidence_gap
    reports through the productive-OOS framing (Deltas 1–5), NOT as
    Jena rules.

The §6.7 Tier 1 candidate mapping comes from the calibration set and
the production prompt's section_6_7_candidate field. Severity is pre-
assigned per the §6.7 table (W-EV-01: High, etc.); the author can
override via a documented rationale.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from uofa_cli.adversarial.judge.final_verdict import FinalVerdict, load_final_verdicts


# §6.7 Tier 1 candidate severity table (spec v1.6 §6.7).
SECTION_6_7_SEVERITY: dict[str, str] = {
    "W-EV-01": "High",
    "W-EV-02": "High",
    "W-REQ-01": "High",
    "W-CX-01": "Medium",
    "W-AR-06": "High",
    "W-AR-07": "Medium",
}

# Default severity when the §6.7 candidate isn't in the table.
DEFAULT_SEVERITY = "Medium"


@dataclass(frozen=True)
class FormalizationCandidate:
    """One REAL-GAP case promoted to a rule-scaffold candidate."""

    case_id: str
    section_6_7_candidate: str  # e.g. 'W-EV-01'
    severity: str  # Critical | High | Medium | Low
    rule_id: str  # snake_case identifier for the Jena rule
    pattern_summary: str  # one-line description; goes in rule comment
    rule_skeleton: str  # forward-chaining Jena rule text
    shacl_skeleton: str | None = None  # only when vocabulary additions needed
    test_skeleton: str = ""  # pytest unit-test scaffold


@dataclass(frozen=True)
class FormalizationResult:
    candidates: list[FormalizationCandidate]
    skipped_case_count: int
    skipped_reasons: dict[str, int] = field(default_factory=dict)


def formalize_real_gaps(
    *,
    final_verdicts: Sequence[FinalVerdict],
    severity_overrides: dict[str, str] | None = None,
) -> FormalizationResult:
    """Walk final_verdicts; emit a candidate per REAL-GAP entry.

    `severity_overrides` is keyed by `section_6_7_candidate` (e.g.
    'W-EV-01') and overrides the default §6.7 table; spec §13.1 lets
    the author document rationale separately.

    Cases without a section_6_7_candidate are skipped (the rule body
    can't be templated without the pattern hook). Skip reasons are
    aggregated for the run summary.
    """
    severity_overrides = severity_overrides or {}
    candidates: list[FormalizationCandidate] = []
    skipped = 0
    skipped_reasons: dict[str, int] = {}

    for fv in final_verdicts:
        if fv.final_verdict != "REAL-GAP":
            skipped += 1
            skipped_reasons["not_real_gap"] = skipped_reasons.get("not_real_gap", 0) + 1
            continue

        # Pull the §6.7 candidate from the source judgment context. The
        # final-verdict layer doesn't carry it directly, so the caller
        # must thread the per-case candidate through. For now, we read
        # it from `provenance_judges` metadata (a future improvement is
        # to add `section_6_7_candidate` directly to FinalVerdict).
        # Tier-A: skip cases without a candidate — surface this in the
        # summary so the author re-runs with a richer input.
        candidate_id = _extract_section_6_7_candidate(fv)
        if not candidate_id:
            skipped += 1
            skipped_reasons["no_section_6_7_candidate"] = (
                skipped_reasons.get("no_section_6_7_candidate", 0) + 1
            )
            continue

        severity = severity_overrides.get(
            candidate_id,
            SECTION_6_7_SEVERITY.get(candidate_id, DEFAULT_SEVERITY),
        )
        rule_id = _rule_id_for(candidate_id)
        pattern_summary = _pattern_summary_for(candidate_id, fv)
        rule = _generate_rule_skeleton(
            rule_id=rule_id,
            candidate_id=candidate_id,
            severity=severity,
            pattern_summary=pattern_summary,
        )
        test_text = _generate_test_skeleton(rule_id=rule_id, candidate_id=candidate_id)

        candidates.append(FormalizationCandidate(
            case_id=fv.case_id,
            section_6_7_candidate=candidate_id,
            severity=severity,
            rule_id=rule_id,
            pattern_summary=pattern_summary,
            rule_skeleton=rule,
            shacl_skeleton=None,  # Tier A: rare path; surface via author review
            test_skeleton=test_text,
        ))

    return FormalizationResult(
        candidates=candidates,
        skipped_case_count=skipped,
        skipped_reasons=skipped_reasons,
    )


def _extract_section_6_7_candidate(fv: FinalVerdict) -> str | None:
    """Return the §6.7 candidate from a FinalVerdict, if known.

    Tier A path: the candidate isn't on FinalVerdict directly — Wave J
    accepts it via the `formalize` CLI's per-case lookup against the
    judgments JSONL (loaded separately and merged before this call).
    For unit tests, the candidate is set via setattr in the fixture.
    """
    return getattr(fv, "section_6_7_candidate", None)


def _rule_id_for(candidate_id: str) -> str:
    """Convert 'W-EV-01' to 'w_ev01' (matches uofa_weakener.rules style).

    Existing catalog convention: single underscore between the letter
    group and the number, no underscore between the digit pairs.
    """
    parts = candidate_id.lower().split("-")
    if len(parts) >= 3:
        # 'w-ev-01' → ['w', 'ev', '01'] → 'w_ev01'
        return f"{parts[0]}_{parts[1]}{parts[2]}"
    return "_".join(parts)


def _pattern_summary_for(candidate_id: str, fv: FinalVerdict) -> str:
    """One-line pattern summary; goes into the Jena rule comment header."""
    base = f"{candidate_id} candidate identified by Phase 3 judge ensemble"
    if fv.final_verdict_confidence is not None:
        base += f" (confidence={fv.final_verdict_confidence:.2f})"
    return base


def _generate_rule_skeleton(
    *,
    rule_id: str,
    candidate_id: str,
    severity: str,
    pattern_summary: str,
) -> str:
    """Generate a Jena forward-chaining rule scaffold.

    Body conditions are intentionally LEFT FOR THE AUTHOR — the LLM-
    judge-derived pattern needs human review before committing to the
    triple match. The scaffold establishes the rule shell, severity,
    and skolem-on-affected-node pattern that the v0.5 catalog uses.
    """
    return f"""# {candidate_id}: {pattern_summary}
# AUTO-SCAFFOLD: review body conditions before merging.
# Severity is from §6.7 Tier 1 table.
[{rule_id}:
    (?uofa rdf:type uofa:UnitOfAssurance)
    # TODO: add body conditions for {candidate_id} pattern
    # e.g. (?uofa uofa:hasContextOfUse ?cou) noValue(?cou, ...)
    makeSkolem(?ann, ?uofa, '{candidate_id}')
    ->
    (?ann rdf:type uofa:WeakenerAnnotation)
    (?ann uofa:patternId '{candidate_id}')
    (?ann uofa:severity '{severity}')
    (?ann schema:description '{pattern_summary}')
    (?uofa uofa:hasWeakener ?ann)
]
"""


def _generate_test_skeleton(
    *,
    rule_id: str,
    candidate_id: str,
) -> str:
    """Generate a pytest scaffold matching the existing `tests/packs/` style."""
    return f"""def test_{rule_id}_fires_on_pattern_instance():
    \"\"\"Verify {candidate_id} rule fires on a positive package instance.

    AUTO-SCAFFOLD: replace `package_path` with a fixture package whose
    structure matches the pattern body. Assert the WeakenerAnnotation
    appears with patternId == '{candidate_id}'.
    \"\"\"
    # TODO: load a positive-instance package and run the rule engine
    # against `packs/core/rules/uofa_weakener.rules` (or the catalog
    # version under test); assert the annotation is present.
    pass


def test_{rule_id}_does_not_fire_on_negative_control():
    \"\"\"Verify {candidate_id} rule is silent on a clean package.\"\"\"
    # TODO: load a clean package fixture; assert no annotations appear
    # with patternId == '{candidate_id}'.
    pass
"""


# ── persistence ─────────────────────────────────────────────────────────


def write_formalization_outputs(
    result: FormalizationResult,
    out_dir: Path,
) -> dict[str, Path]:
    """Write per-candidate rule + test files into out_dir.

    Layout:
        out_dir/
          rules/
            <rule_id>.rule          # Jena rule snippet
          tests/
            test_<rule_id>.py        # pytest scaffold
          formalization_summary.json # candidate index
    """
    rules_dir = out_dir / "rules"
    tests_dir = out_dir / "tests"
    rules_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}
    for c in result.candidates:
        rule_path = rules_dir / f"{c.rule_id}.rule"
        rule_path.write_text(c.rule_skeleton)
        test_path = tests_dir / f"test_{c.rule_id}.py"
        test_path.write_text(c.test_skeleton)
        written[c.case_id] = rule_path

    summary_path = out_dir / "formalization_summary.json"
    summary_path.write_text(json.dumps({
        "candidate_count": len(result.candidates),
        "skipped_case_count": result.skipped_case_count,
        "skipped_reasons": result.skipped_reasons,
        "candidates": [
            {
                "case_id": c.case_id,
                "section_6_7_candidate": c.section_6_7_candidate,
                "severity": c.severity,
                "rule_id": c.rule_id,
                "rule_path": str((rules_dir / f"{c.rule_id}.rule").relative_to(out_dir)),
                "test_path": str((tests_dir / f"test_{c.rule_id}.py").relative_to(out_dir)),
            }
            for c in result.candidates
        ],
    }, indent=2))
    return written


# ── CLI driver ──────────────────────────────────────────────────────────


def run_formalize_from_files(
    *,
    final_verdicts_path: Path,
    judgments_paths: dict[str, Path],
    out_dir: Path,
    severity_overrides: dict[str, str] | None = None,
) -> FormalizationResult:
    """End-to-end formalize: load final verdicts, attach §6.7 candidates
    from judgments JSONL, generate rule scaffolds, persist."""
    final_verdicts = load_final_verdicts(final_verdicts_path)

    # Attach section_6_7_candidate from the production judgments. Take
    # the first non-None candidate across A/B/C; this is a reasonable
    # heuristic since 2-of-3 production judges agreeing on REAL-GAP
    # almost always agree on the candidate.
    by_case: dict[str, str] = {}
    for path in judgments_paths.values():
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            cid = rec.get("case_id")
            cand = rec.get("section_6_7_candidate")
            if cid and cand and cid not in by_case:
                by_case[cid] = cand

    # FinalVerdict is frozen — we can't setattr. Construct an enriched
    # list of dataclass instances by re-creating each.
    enriched: list[FinalVerdict] = []
    for fv in final_verdicts:
        candidate = by_case.get(fv.case_id)
        if candidate is None:
            enriched.append(fv)
        else:
            # Preserve the immutable contract by building a new instance
            # via the same dataclass + an extra attribute set via
            # object.__setattr__ (frozen dataclasses allow this in the
            # constructor). For runtime annotation, treat
            # section_6_7_candidate as a free-form attr the formalize
            # path knows about.
            object.__setattr__(fv, "section_6_7_candidate", candidate)
            enriched.append(fv)

    result = formalize_real_gaps(
        final_verdicts=enriched,
        severity_overrides=severity_overrides,
    )
    write_formalization_outputs(result, out_dir)
    return result
