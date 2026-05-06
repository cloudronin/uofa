"""Final-verdict assembly across CONVERGENT / ARBITRATED / AUTHOR layers
(spec v1.6 §10.3, productive-OOS Delta 5).

Sources verdicts in priority order:
  1. AUTHOR_OVERRIDE — author-side spot-check correction over a CONVERGENT case.
  2. AUTHOR_FINAL    — author final verdict on the escalation queue.
  3. ARBITRATED      — Judge E verdict where Judge E confidence ≥ floor.
  4. CONVERGENT      — production-judge majority where all agreeing
                       judges meet the confidence floor.

For OUT-OF-SCOPE verdicts the productive-OOS evidence_gap carries through
with explicit source attribution (Delta 5):
  - CONVERGENT OOS: primary gap from the highest-confidence agreeing
    judge; ties broken by canonical A→B→C ordering; alternatives
    preserved in `alternative_evidence_gaps` for transparency.
  - ARBITRATED OOS: gap sourced from Judge E.
  - AUTHOR_FINAL / AUTHOR_OVERRIDE OOS: gap sourced from the author
    adjudication record.

The final_verdicts.jsonl schema is the single source-of-truth output for
audit-engineer-facing reports; downstream Stage 5 formalization (Wave J)
reads it to scaffold Jena rules from REAL-GAP cases.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from uofa_cli.adversarial.judge.providers.base import Judgment


# Production-judge canonical ordering for tie-breaks per Delta 5.
PRODUCTION_POSITIONS: tuple[str, ...] = ("A", "B", "C")


@dataclass(frozen=True)
class EvidenceGap:
    """OUT-OF-SCOPE evidence_gap with source attribution (Delta 5)."""

    missing_evidence_type: str
    would_support_defeater_evaluation: str
    evidence_gap_source: str  # judge_a | judge_b | judge_c | judge_e | author


@dataclass(frozen=True)
class FinalVerdict:
    """One row of final_verdicts.jsonl.

    `provenance` ∈ {CONVERGENT, ARBITRATED, AUTHOR_FINAL, AUTHOR_OVERRIDE}.
    `provenance_judges` lists the judge labels that produced the verdict
    (e.g. ['A', 'B'] for a 2-of-3 CONVERGENT, ['E'] for ARBITRATED).
    `evidence_gap` is populated only when final_verdict == 'OUT-OF-SCOPE'.
    `alternative_evidence_gaps` carries additional OOS gap text from
    other judges in CONVERGENT cases for transparency.
    """

    case_id: str
    final_verdict: str
    provenance: str
    provenance_judges: tuple[str, ...]
    final_verdict_confidence: float | None
    evidence_gap: EvidenceGap | None = None
    alternative_evidence_gaps: tuple[EvidenceGap, ...] = field(default_factory=tuple)


def _gap_from_judgment(judgment: Judgment, source: str) -> EvidenceGap | None:
    """Pull evidence_gap off a Judgment when present.

    Judgment is a dataclass; the v1.6 schema attaches evidence_gap as an
    optional dict on the response. Producers stash it in the
    `judge_model_params` extras OR a top-level `evidence_gap` attribute
    set on parse. We tolerate both shapes here.
    """
    raw = getattr(judgment, "evidence_gap", None)
    if raw is None:
        # Some serialization paths drop the optional attr; check params.
        params = getattr(judgment, "judge_model_params", None) or {}
        raw = params.get("evidence_gap")
    if not raw:
        return None
    met = raw.get("missing_evidence_type")
    sup = raw.get("would_support_defeater_evaluation")
    if not met or not sup:
        return None
    return EvidenceGap(
        missing_evidence_type=met,
        would_support_defeater_evaluation=sup,
        evidence_gap_source=source,
    )


def _gap_from_dict(record: Mapping[str, object], source: str) -> EvidenceGap | None:
    """Pull evidence_gap off an author/arbitration record dict."""
    raw = record.get("evidence_gap")
    if not isinstance(raw, Mapping):
        return None
    met = raw.get("missing_evidence_type")
    sup = raw.get("would_support_defeater_evaluation")
    if not isinstance(met, str) or not isinstance(sup, str) or not met or not sup:
        return None
    return EvidenceGap(
        missing_evidence_type=met,
        would_support_defeater_evaluation=sup,
        evidence_gap_source=source,
    )


def _select_convergent_oos_gap(
    agreeing: Sequence[tuple[str, Judgment]],
) -> tuple[EvidenceGap | None, tuple[EvidenceGap, ...]]:
    """Pick the primary evidence_gap and alternatives for a CONVERGENT OOS.

    Per Delta 5: highest-confidence judge primary; ties broken by canonical
    A→B→C order. All other agreeing judges' gap text becomes alternatives.

    `agreeing` is a list of (position, judgment) where position ∈ A/B/C
    and the judgments share verdict='OUT-OF-SCOPE'.
    """
    # Pre-collect each agreeing judge's gap (some may be missing entirely).
    gaps: list[tuple[str, EvidenceGap, float]] = []
    for pos, j in agreeing:
        gap = _gap_from_judgment(j, f"judge_{pos.lower()}")
        if gap is not None:
            gaps.append((pos, gap, j.confidence))

    if not gaps:
        return None, ()

    # Sort: highest confidence first; then canonical position order.
    pos_priority = {p: i for i, p in enumerate(PRODUCTION_POSITIONS)}
    gaps.sort(key=lambda x: (-x[2], pos_priority.get(x[0], 99)))
    primary = gaps[0][1]
    alternatives = tuple(g for _, g, _ in gaps[1:])
    return primary, alternatives


def assemble_final_verdicts(
    *,
    triage_entries: Iterable[object],  # TriageEntry, but avoid circular import
    arbitration_records: Mapping[str, Mapping[str, object]] | None = None,
    author_records: Mapping[str, Mapping[str, object]] | None = None,
    spot_check_overrides: Mapping[str, Mapping[str, object]] | None = None,
    confidence_floor: float = 0.6,
) -> list[FinalVerdict]:
    """Assemble final verdicts across the four-layer source priority.

    Inputs:
      - triage_entries: list of `TriageEntry` from `triage_corpus`. Each
        entry has bucket (CONVERGENT/DISAGREEMENT), majority_verdict,
        and the (A, B, C) judgment trio.
      - arbitration_records: dict[case_id → {"verdict", "confidence",
        "evidence_gap"}] from Judge E. Optional.
      - author_records: dict[case_id → {"final_verdict", "evidence_gap",
        "rationale"}] from author final verdicts. Optional. Includes
        BOTH escalation queue entries and any author overrides; keyed
        by case_id alone (caller is expected to disambiguate).
      - spot_check_overrides: dict[case_id → {"override_verdict",
        "evidence_gap", "rationale", "original_verdict"}] from author
        spot-check on CONVERGENT cases. Optional.

    Returns a list of FinalVerdict in triage_entries order.
    """
    arbitration_records = arbitration_records or {}
    author_records = author_records or {}
    spot_check_overrides = spot_check_overrides or {}

    out: list[FinalVerdict] = []
    for entry in triage_entries:
        case_id = entry.case_id
        ja, jb, jc = entry.judgments

        # ── 1. AUTHOR_OVERRIDE (CONVERGENT case the author corrected) ──
        if case_id in spot_check_overrides:
            rec = spot_check_overrides[case_id]
            override_verdict = rec.get("override_verdict")
            if override_verdict:
                out.append(_build_author(
                    case_id=case_id,
                    verdict=override_verdict,
                    record=rec,
                    provenance="AUTHOR_OVERRIDE",
                ))
                continue

        # ── 2. AUTHOR_FINAL (escalation-queue cases the author resolved) ──
        if case_id in author_records:
            rec = author_records[case_id]
            final_verdict = rec.get("final_verdict")
            if final_verdict:
                out.append(_build_author(
                    case_id=case_id,
                    verdict=final_verdict,
                    record=rec,
                    provenance="AUTHOR_FINAL",
                ))
                continue

        # ── 3. ARBITRATED (Judge E ≥ floor) ──
        if case_id in arbitration_records:
            rec = arbitration_records[case_id]
            conf = float(rec.get("confidence", 0.0))
            if conf >= confidence_floor:
                out.append(_build_arbitrated(case_id=case_id, record=rec))
                continue
            # Below floor → ESCALATED. If author hasn't resolved yet,
            # fall through; the caller may emit an UNRESOLVED placeholder.

        # ── 4. CONVERGENT (production majority) ──
        from uofa_cli.adversarial.judge.triage import TriageBucket  # avoid cycle
        if entry.bucket == TriageBucket.CONVERGENT and entry.majority_verdict:
            agreeing_positions: list[tuple[str, Judgment]] = [
                ("A", ja), ("B", jb), ("C", jc)
            ]
            agreeing = [
                (pos, j) for pos, j in agreeing_positions
                if j.verdict == entry.majority_verdict
            ]
            confidences = [j.confidence for _, j in agreeing]
            avg_conf = sum(confidences) / len(confidences) if confidences else None

            evidence_gap: EvidenceGap | None = None
            alternative_gaps: tuple[EvidenceGap, ...] = ()
            if entry.majority_verdict == "OUT-OF-SCOPE":
                evidence_gap, alternative_gaps = _select_convergent_oos_gap(agreeing)

            out.append(FinalVerdict(
                case_id=case_id,
                final_verdict=entry.majority_verdict,
                provenance="CONVERGENT",
                provenance_judges=tuple(p for p, _ in agreeing),
                final_verdict_confidence=avg_conf,
                evidence_gap=evidence_gap,
                alternative_evidence_gaps=alternative_gaps,
            ))
            continue

        # ── DISAGREEMENT with no resolution path ──
        # Stage 4 author intake should have surfaced this; emit an
        # UNRESOLVED row so the consumer notices.
        out.append(FinalVerdict(
            case_id=case_id,
            final_verdict="UNRESOLVED",
            provenance="UNRESOLVED",
            provenance_judges=(),
            final_verdict_confidence=None,
            evidence_gap=None,
            alternative_evidence_gaps=(),
        ))

    return out


def _build_arbitrated(*, case_id: str, record: Mapping[str, object]) -> FinalVerdict:
    """Build an ARBITRATED final verdict from a Judge E record."""
    verdict = str(record["verdict"])
    confidence = float(record.get("confidence", 0.0))
    gap: EvidenceGap | None = None
    if verdict == "OUT-OF-SCOPE":
        gap = _gap_from_dict(record, "judge_e")
    return FinalVerdict(
        case_id=case_id,
        final_verdict=verdict,
        provenance="ARBITRATED",
        provenance_judges=("E",),
        final_verdict_confidence=confidence,
        evidence_gap=gap,
    )


def _build_author(
    *,
    case_id: str,
    verdict: str,
    record: Mapping[str, object],
    provenance: str,
) -> FinalVerdict:
    """Build an AUTHOR_FINAL or AUTHOR_OVERRIDE final verdict."""
    gap: EvidenceGap | None = None
    if verdict == "OUT-OF-SCOPE":
        gap = _gap_from_dict(record, "author")
    confidence_raw = record.get("confidence")
    confidence = float(confidence_raw) if isinstance(confidence_raw, (int, float)) else None
    return FinalVerdict(
        case_id=case_id,
        final_verdict=verdict,
        provenance=provenance,
        provenance_judges=("AUTHOR",),
        final_verdict_confidence=confidence,
        evidence_gap=gap,
    )


# ── persistence ─────────────────────────────────────────────────────────


def write_final_verdicts(
    final_verdicts: Sequence[FinalVerdict], path: Path
) -> None:
    """Write final_verdicts.jsonl (one JSON object per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for fv in final_verdicts:
            d: dict = {
                "case_id": fv.case_id,
                "final_verdict": fv.final_verdict,
                "provenance": fv.provenance,
                "provenance_judges": list(fv.provenance_judges),
                "final_verdict_confidence": fv.final_verdict_confidence,
            }
            if fv.evidence_gap is not None:
                d["evidence_gap"] = asdict(fv.evidence_gap)
            if fv.alternative_evidence_gaps:
                d["alternative_evidence_gaps"] = [
                    asdict(g) for g in fv.alternative_evidence_gaps
                ]
            f.write(json.dumps(d) + "\n")


def load_final_verdicts(path: Path) -> list[FinalVerdict]:
    """Read final_verdicts.jsonl back into FinalVerdict records."""
    out: list[FinalVerdict] = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        gap = None
        gap_raw = d.get("evidence_gap")
        if gap_raw:
            gap = EvidenceGap(**gap_raw)
        alts = tuple(
            EvidenceGap(**g) for g in d.get("alternative_evidence_gaps", []) or []
        )
        out.append(FinalVerdict(
            case_id=d["case_id"],
            final_verdict=d["final_verdict"],
            provenance=d["provenance"],
            provenance_judges=tuple(d.get("provenance_judges", []) or []),
            final_verdict_confidence=d.get("final_verdict_confidence"),
            evidence_gap=gap,
            alternative_evidence_gaps=alts,
        ))
    return out


# ── spot-check overrides loader ─────────────────────────────────────────


def load_spot_check_overrides(path: Path) -> dict[str, dict]:
    """Read spot_check_overrides.jsonl indexed by case_id.

    Schema (spec v1.6 §11.4):
      {
        "case_id": str,
        "original_verdict": str,
        "override_verdict": str,
        "override_rationale": str,
        "original_provenance": str (e.g. "CONVERGENT"),
        "evidence_gap": optional dict (when override_verdict=OUT-OF-SCOPE)
      }
    """
    by_case: dict[str, dict] = {}
    if not path.exists():
        return by_case
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "case_id" in rec:
            by_case[rec["case_id"]] = rec
    return by_case


def load_author_records(path: Path) -> dict[str, dict]:
    """Read author final-verdict JSONL indexed by case_id."""
    by_case: dict[str, dict] = {}
    if not path.exists():
        return by_case
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "case_id" in rec:
            by_case[rec["case_id"]] = rec
    return by_case


def load_arbitration_records(path: Path) -> dict[str, dict]:
    """Read judgments_E.jsonl indexed by case_id (subset of arbitration.py
    loader; here we keep raw JSON dicts for evidence_gap pass-through)."""
    by_case: dict[str, dict] = {}
    if not path.exists():
        return by_case
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "case_id" in rec:
            by_case[rec["case_id"]] = rec
    return by_case
