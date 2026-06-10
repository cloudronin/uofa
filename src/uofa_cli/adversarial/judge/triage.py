"""Majority-of-3 inter-judge triage (spec v1.6 §10.1).

Three-judge ensembles partition cases into TWO buckets in v1.6 (down
from three in v1.5; the UNCERTAIN bin is folded into DISAGREEMENT):

  CONVERGENT    ≥ 2 agree on a verdict, with all agreeing judges at
                confidence ≥ confidence_floor (default 0.6)
  DISAGREEMENT  - all three disagree, OR
                - two disagree + one UNCERTAIN, OR
                - ≥ 2 agree but at least one agreeing judge below
                  confidence_floor, OR
                - ≥ 2 of 3 return UNCERTAIN (v1.6 fold; was its own bin)

DISAGREEMENT cases route to Judge E arbitration (Stage 3b, spec §10.2).
The `disagreement_subtype` field preserves the v1.5 sub-pattern for
diagnostic value:

  - convergent_2of3 / convergent_3of3
  - all_three_disagree
  - two_disagree_one_uncertain
  - low_conf_concurrence_2of3 / low_conf_concurrence_3of3
  - uncertain_majority_2of3 / uncertain_majority_3of3
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from uofa_cli.adversarial.judge.providers.base import Judgment


# Spec §10.1 default confidence floor below which an agreeing verdict
# is considered low-confidence and routes to DIVERGENT.
DEFAULT_CONFIDENCE_FLOOR = 0.6


# Spec Part 3.1 default: below this confidence a *forced* (non-UNCERTAIN)
# verdict is treated as low-confidence, and the case is additionally routed
# to the adjudication queue even when majority logic calls it CONVERGENT.
DEFAULT_LOW_CONFIDENCE_ROUTE_THRESHOLD = 0.5


class TriageBucket(str, Enum):
    """v1.6: two-bucket partition. UNCERTAIN folds into DISAGREEMENT."""
    CONVERGENT = "CONVERGENT"
    DISAGREEMENT = "DISAGREEMENT"
    # Legacy v1.5 names retained as aliases for downstream code that
    # hasn't migrated yet. New code should use CONVERGENT/DISAGREEMENT.
    DIVERGENT = "DISAGREEMENT"
    UNCERTAIN = "DISAGREEMENT"


@dataclass(frozen=True)
class TriageEntry:
    """One case's triage outcome.

    `case_id` is the bundle case id; `verdicts` is the per-position
    (A, B, C) verdict tuple; `bucket` is the triage assignment.
    `majority_verdict` is the verdict the bucket "votes" for if any
    (None on full disagreement).
    """

    case_id: str
    judgments: tuple[Judgment, Judgment, Judgment]
    bucket: TriageBucket
    majority_verdict: str | None
    disagreement_type: str  # short label for the queue UI


@dataclass(frozen=True)
class TriageResult:
    """Aggregate triage over a corpus of (A, B, C) judgment trios."""

    entries: list[TriageEntry]
    bucket_counts: dict[TriageBucket, int]


def triage_case(
    judgment_a: Judgment,
    judgment_b: Judgment,
    judgment_c: Judgment,
    *,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> TriageEntry:
    """Triage a single (A, B, C) judgment trio per §10.1.

    All three judgments must reference the same case_id; otherwise
    raises ValueError. Verdicts are matched as exact strings (e.g.
    'REAL-GAP'); confidence as a float in [0, 1].
    """
    if not (judgment_a.case_id == judgment_b.case_id == judgment_c.case_id):
        raise ValueError(
            f"trio has mismatched case ids: "
            f"A={judgment_a.case_id}, B={judgment_b.case_id}, C={judgment_c.case_id}"
        )

    case_id = judgment_a.case_id
    judgments = (judgment_a, judgment_b, judgment_c)

    # ── UNCERTAIN majority (≥ 2 UNCERTAIN) — v1.6 folds into DISAGREEMENT ──
    uncertain_count = sum(1 for j in judgments if j.verdict == "UNCERTAIN")
    if uncertain_count >= 2:
        return TriageEntry(
            case_id=case_id,
            judgments=judgments,
            bucket=TriageBucket.DISAGREEMENT,
            majority_verdict="UNCERTAIN",
            disagreement_type=f"uncertain_majority_{uncertain_count}of3",
        )

    # ── majority-of-3 verdict tally ──
    verdict_counts = Counter(j.verdict for j in judgments)
    most_common = verdict_counts.most_common(1)[0]
    majority_verdict, majority_count = most_common

    if majority_count >= 2:
        # Confidence floor gate: every agreeing judge must be ≥ floor.
        agreeing = [j for j in judgments if j.verdict == majority_verdict]
        if all(j.confidence >= confidence_floor for j in agreeing):
            return TriageEntry(
                case_id=case_id,
                judgments=judgments,
                bucket=TriageBucket.CONVERGENT,
                majority_verdict=majority_verdict,
                disagreement_type=f"convergent_{majority_count}of3",
            )
        # Low-confidence concurrence routes to DISAGREEMENT (v1.6 §10.1).
        return TriageEntry(
            case_id=case_id,
            judgments=judgments,
            bucket=TriageBucket.DISAGREEMENT,
            majority_verdict=None,
            disagreement_type=f"low_conf_concurrence_{majority_count}of3",
        )

    # ── all three disagree ──
    if uncertain_count == 1:
        return TriageEntry(
            case_id=case_id,
            judgments=judgments,
            bucket=TriageBucket.DISAGREEMENT,
            majority_verdict=None,
            disagreement_type="two_disagree_one_uncertain",
        )
    return TriageEntry(
        case_id=case_id,
        judgments=judgments,
        bucket=TriageBucket.DISAGREEMENT,
        majority_verdict=None,
        disagreement_type="all_three_disagree",
    )


def triage_corpus(
    trios: list[tuple[Judgment, Judgment, Judgment]],
    *,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> TriageResult:
    """Triage a corpus of (A, B, C) judgment trios.

    Trios must be aligned: index i in each judge's list refers to the
    same case_id. Use `align_trios` to build a list of trios from per-
    judge `Judgment` lists keyed by case_id.
    """
    entries = [triage_case(*trio, confidence_floor=confidence_floor) for trio in trios]
    counts: dict[TriageBucket, int] = {b: 0 for b in TriageBucket}
    for e in entries:
        counts[e.bucket] += 1
    return TriageResult(entries=entries, bucket_counts=counts)


def align_trios(
    judgments_a: list[Judgment],
    judgments_b: list[Judgment],
    judgments_c: list[Judgment],
) -> list[tuple[Judgment, Judgment, Judgment]]:
    """Align three per-judge judgment lists by case_id.

    Returns one (A, B, C) trio per case_id present in ALL three lists.
    Cases missing from any judge are dropped (logged via warnings.warn);
    Stage 4 reports the dropped count alongside agreement statistics.
    """
    by_a = {j.case_id: j for j in judgments_a}
    by_b = {j.case_id: j for j in judgments_b}
    by_c = {j.case_id: j for j in judgments_c}

    common = sorted(set(by_a) & set(by_b) & set(by_c))
    return [(by_a[k], by_b[k], by_c[k]) for k in common]


def is_low_confidence_forced(
    entry: TriageEntry,
    *,
    threshold: float = DEFAULT_LOW_CONFIDENCE_ROUTE_THRESHOLD,
) -> bool:
    """True if any judge in the trio emitted a forced verdict below threshold.

    A "forced" verdict is any committed verdict class other than UNCERTAIN.
    Per spec Part 3.1, a forced verdict held below `threshold` signals the
    judge is not actually committed; such a case routes into the adjudication
    queue alongside DISAGREEMENT cases, compensating for judges that
    under-emit UNCERTAIN in production.

    Read-only predicate over an already-triaged entry. It does NOT participate
    in bucket assignment (`triage_case` is unchanged); it only governs whether
    `run_triage` additionally writes an otherwise-CONVERGENT entry to the queue.
    """
    return any(
        j.verdict != "UNCERTAIN" and j.confidence < threshold
        for j in entry.judgments
    )
