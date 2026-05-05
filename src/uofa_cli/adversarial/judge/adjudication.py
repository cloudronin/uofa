"""Inter-judge agreement statistics + author adjudication helpers (spec v1.6 §12).

Computes:
  - Pairwise Cohen's κ (sklearn.metrics.cohen_kappa_score) for each of
    AB / AC / BC; per-pair acceptance target ≥ 0.70 (§8.3, §12.1).
  - Fleiss' κ across all three judges (statsmodels); ensemble target ≥ 0.65.
  - Confusion matrices for each judge pair plus author-vs-each-judge.

v1.6 additions (Wave D, plan item 27):
  - EA / EB / EC confusion matrices (Judge E vs each production judge on
    the disagreement queue).
  - author_E confusion matrix (author final verdict vs Judge E on the
    escalation queue).
  - Judge E vs Judge D agreement on the calibration set (per-class match
    rate; spec §8.0 reports this informationally — no acceptance threshold).
  - Author spot-check override rate (target ≤ 10% per §11.4).

The most common bug in Fleiss' κ implementations is feeding raw labels
where statsmodels expects an (n_subjects, n_categories) count matrix.
The `_to_count_matrix` helper handles that reshape.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Mapping, Sequence

# Spec verdict classes; fixed ordering for confusion-matrix axes.
VERDICT_CLASSES: tuple[str, ...] = (
    "CORRECT-DETECTION",
    "REAL-GAP",
    "GENERATOR-ARTIFACT",
    "EXISTING-RULE-MISBEHAVIOR",
    "OUT-OF-SCOPE",
    "UNCERTAIN",
)


@dataclass(frozen=True)
class AgreementStats:
    """Aggregate inter-judge agreement statistics over a triaged corpus."""

    case_count: int
    cohen_kappa_AB: float
    cohen_kappa_AC: float
    cohen_kappa_BC: float
    fleiss_kappa: float
    raw_agreement_at_least_2of3: float


def cohen_kappa(verdicts_x: Sequence[str], verdicts_y: Sequence[str]) -> float:
    """Cohen's κ between two judges' aligned verdict lists.

    Uses sklearn.metrics.cohen_kappa_score with the fixed VERDICT_CLASSES
    label set so degenerate cases (all-agree on one class) return κ = 1.0
    deterministically rather than NaN.
    """
    if len(verdicts_x) != len(verdicts_y):
        raise ValueError(
            f"cohen_kappa: verdicts_x and verdicts_y differ in length "
            f"({len(verdicts_x)} vs {len(verdicts_y)})"
        )
    if not verdicts_x:
        return float("nan")  # undefined on empty input

    from sklearn.metrics import cohen_kappa_score

    return float(cohen_kappa_score(verdicts_x, verdicts_y, labels=list(VERDICT_CLASSES)))


def _to_count_matrix(verdicts_per_case: Sequence[Sequence[str]]) -> list[list[int]]:
    """Reshape per-case verdict lists into a Fleiss-compatible count matrix.

    Input: a sequence of length n_cases, where each element is a sequence
    of n_raters labels (one per rater).
    Output: a list of length n_cases, where each element is a list of
    counts indexed by VERDICT_CLASSES.

    Example for 3 raters voting on 2 cases:
        verdicts_per_case = [
            ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT"],
            ["UNCERTAIN", "UNCERTAIN", "UNCERTAIN"],
        ]
        →
        [
            [0, 2, 1, 0, 0, 0],   # 0 CORRECT, 2 REAL-GAP, 1 GEN-ART, ...
            [0, 0, 0, 0, 0, 3],   # 3 UNCERTAIN
        ]

    This is the input shape `statsmodels.stats.inter_rater.fleiss_kappa`
    expects; the function is a common-bug wedge.
    """
    out: list[list[int]] = []
    for case_verdicts in verdicts_per_case:
        counts = Counter(case_verdicts)
        # Validate every label is in VERDICT_CLASSES; an unknown label
        # would silently drop in the Counter and skew kappa.
        for v in case_verdicts:
            if v not in VERDICT_CLASSES:
                raise ValueError(
                    f"unknown verdict {v!r}; expected one of {VERDICT_CLASSES}"
                )
        out.append([counts.get(cls, 0) for cls in VERDICT_CLASSES])
    return out


def fleiss_kappa(verdicts_per_case: Sequence[Sequence[str]]) -> float:
    """Fleiss' κ across N raters and M cases.

    `verdicts_per_case[i][r]` is rater r's verdict on case i. All cases
    must have the same number of raters.
    """
    if not verdicts_per_case:
        return float("nan")
    n_raters = len(verdicts_per_case[0])
    if any(len(c) != n_raters for c in verdicts_per_case):
        raise ValueError("fleiss_kappa: all cases must have the same number of raters")

    matrix = _to_count_matrix(verdicts_per_case)

    from statsmodels.stats.inter_rater import fleiss_kappa as _fk

    return float(_fk(matrix))


def confusion_matrix(
    verdicts_x: Sequence[str], verdicts_y: Sequence[str]
) -> list[list[int]]:
    """Confusion matrix indexed by VERDICT_CLASSES (X = rows, Y = cols).

    Returns a 6×6 list-of-lists. Use for per-pair Stage 4 outputs
    (`confusion_matrix_AB.csv` etc.) and for author-vs-judge matrices.
    """
    from sklearn.metrics import confusion_matrix as _cm

    return _cm(verdicts_x, verdicts_y, labels=list(VERDICT_CLASSES)).tolist()


def compute_agreement(
    judgments_a: Sequence[str],
    judgments_b: Sequence[str],
    judgments_c: Sequence[str],
) -> AgreementStats:
    """Compute the full Stage 4 agreement table from three aligned verdict lists.

    Lists must be the same length and aligned by case (verdicts_x[i] is
    judge X's verdict on case i for the same i across X ∈ {A,B,C}).
    """
    n = len(judgments_a)
    if not (n == len(judgments_b) == len(judgments_c)):
        raise ValueError(
            f"compute_agreement: per-judge lists differ in length "
            f"({n}, {len(judgments_b)}, {len(judgments_c)})"
        )

    if n == 0:
        return AgreementStats(
            case_count=0,
            cohen_kappa_AB=float("nan"),
            cohen_kappa_AC=float("nan"),
            cohen_kappa_BC=float("nan"),
            fleiss_kappa=float("nan"),
            raw_agreement_at_least_2of3=0.0,
        )

    # Fleiss expects a list of [a_verdict, b_verdict, c_verdict] per case.
    per_case = [list(t) for t in zip(judgments_a, judgments_b, judgments_c)]

    raw_2of3 = 0
    for trio in per_case:
        if len(set(trio)) <= 2:  # at least two raters agree
            most_common = Counter(trio).most_common(1)[0][1]
            if most_common >= 2:
                raw_2of3 += 1

    return AgreementStats(
        case_count=n,
        cohen_kappa_AB=cohen_kappa(judgments_a, judgments_b),
        cohen_kappa_AC=cohen_kappa(judgments_a, judgments_c),
        cohen_kappa_BC=cohen_kappa(judgments_b, judgments_c),
        fleiss_kappa=fleiss_kappa(per_case),
        raw_agreement_at_least_2of3=raw_2of3 / n,
    )


# ── v1.6 additions: Judge E + Judge D + author final-verdict metrics ──


@dataclass(frozen=True)
class JudgeEStats:
    """Judge E (arbiter) agreement metrics over the disagreement queue.

    Per spec v1.6 §12.2:
      - cohen_kappa_E[A|B|C]: Judge E vs each production judge on the
        disagreement queue subset (informational; no threshold).
      - confusion_matrix_E[A|B|C]: 6×6 matrix per VERDICT_CLASSES.
      - judge_e_arbitrated_count / escalated_count: stage-3b partition
        cardinality at the run's confidence floor (default 0.6).
    """

    case_count: int
    cohen_kappa_EA: float
    cohen_kappa_EB: float
    cohen_kappa_EC: float
    confusion_matrix_EA: list[list[int]]
    confusion_matrix_EB: list[list[int]]
    confusion_matrix_EC: list[list[int]]
    arbitrated_count: int
    escalated_count: int


@dataclass(frozen=True)
class AuthorAdjudicationStats:
    """Author-side metrics (spec v1.6 §12.2 + §11.4).

    `confusion_matrix_author_E` covers ESCALATED cases where Judge E
    confidence < floor and the author rendered a final verdict.
    `spot_check_override_rate` is over CONVERGENT cases the author
    spot-checked; target ≤ 0.10 per spec §11.4.
    """

    escalated_case_count: int
    confusion_matrix_author_E: list[list[int]]
    spot_check_total: int
    spot_check_override_count: int
    spot_check_override_rate: float


@dataclass(frozen=True)
class JudgeDAgreementStats:
    """Judge E vs Judge D agreement on the calibration set (spec §8.0).

    Per-class match rate is informational only — no acceptance threshold
    applies, since Judge D is the calibration anchor and Judge E is the
    arbiter. The metric surfaces methodological independence.
    """

    case_count: int
    overall_match_rate: float
    per_class_match_rate: dict[str, float] = field(default_factory=dict)


def compute_judge_e_agreement(
    *,
    judgments_a: Sequence[str],
    judgments_b: Sequence[str],
    judgments_c: Sequence[str],
    judgments_e: Sequence[str],
    arbitrated_count: int = 0,
    escalated_count: int = 0,
) -> JudgeEStats:
    """Judge E confusion matrices + κ vs each production judge.

    Inputs are aligned verdict lists over the disagreement queue subset
    (one entry per case, in matching order across the four sequences).
    """
    n = len(judgments_e)
    if not (n == len(judgments_a) == len(judgments_b) == len(judgments_c)):
        raise ValueError(
            "compute_judge_e_agreement: per-judge lists differ in length "
            f"({n}, {len(judgments_a)}, {len(judgments_b)}, {len(judgments_c)})"
        )

    if n == 0:
        empty = [[0] * len(VERDICT_CLASSES) for _ in VERDICT_CLASSES]
        return JudgeEStats(
            case_count=0,
            cohen_kappa_EA=float("nan"),
            cohen_kappa_EB=float("nan"),
            cohen_kappa_EC=float("nan"),
            confusion_matrix_EA=empty,
            confusion_matrix_EB=empty,
            confusion_matrix_EC=empty,
            arbitrated_count=arbitrated_count,
            escalated_count=escalated_count,
        )

    return JudgeEStats(
        case_count=n,
        cohen_kappa_EA=cohen_kappa(judgments_e, judgments_a),
        cohen_kappa_EB=cohen_kappa(judgments_e, judgments_b),
        cohen_kappa_EC=cohen_kappa(judgments_e, judgments_c),
        confusion_matrix_EA=confusion_matrix(judgments_e, judgments_a),
        confusion_matrix_EB=confusion_matrix(judgments_e, judgments_b),
        confusion_matrix_EC=confusion_matrix(judgments_e, judgments_c),
        arbitrated_count=arbitrated_count,
        escalated_count=escalated_count,
    )


def compute_author_adjudication(
    *,
    author_verdicts: Sequence[str],
    judge_e_verdicts: Sequence[str],
    spot_check_total: int = 0,
    spot_check_override_count: int = 0,
) -> AuthorAdjudicationStats:
    """Author final verdict vs Judge E on the escalation queue.

    `author_verdicts[i]` and `judge_e_verdicts[i]` align by escalated
    case index. Spot-check counts apply over CONVERGENT cases the author
    sampled per §11.4 — separate from the escalation queue.
    """
    n = len(author_verdicts)
    if n != len(judge_e_verdicts):
        raise ValueError(
            "compute_author_adjudication: author and judge_e lists differ in "
            f"length ({n} vs {len(judge_e_verdicts)})"
        )

    cm = (
        confusion_matrix(author_verdicts, judge_e_verdicts)
        if n
        else [[0] * len(VERDICT_CLASSES) for _ in VERDICT_CLASSES]
    )
    rate = (
        (spot_check_override_count / spot_check_total)
        if spot_check_total > 0
        else 0.0
    )
    return AuthorAdjudicationStats(
        escalated_case_count=n,
        confusion_matrix_author_E=cm,
        spot_check_total=spot_check_total,
        spot_check_override_count=spot_check_override_count,
        spot_check_override_rate=rate,
    )


def compute_judge_e_vs_d_agreement(
    *,
    judge_e_verdicts: Sequence[str],
    judge_d_verdicts: Sequence[str],
) -> JudgeDAgreementStats:
    """Per-class match rate Judge E vs Judge D on the calibration set.

    Both sequences must align by case index (same calibration case at
    the same position). Per-class rate is `correct / total` keyed by
    Judge D's verdict class; classes with zero Judge D entries are
    omitted from the dict. Overall is `correct / total`.
    """
    n = len(judge_e_verdicts)
    if n != len(judge_d_verdicts):
        raise ValueError(
            "compute_judge_e_vs_d_agreement: lists differ in length "
            f"({n} vs {len(judge_d_verdicts)})"
        )
    if n == 0:
        return JudgeDAgreementStats(
            case_count=0, overall_match_rate=float("nan"), per_class_match_rate={}
        )

    overall_correct = 0
    per_class_total: dict[str, int] = {}
    per_class_correct: dict[str, int] = {}
    for e_v, d_v in zip(judge_e_verdicts, judge_d_verdicts):
        if d_v not in VERDICT_CLASSES:
            raise ValueError(f"unknown verdict {d_v!r}; expected one of {VERDICT_CLASSES}")
        per_class_total[d_v] = per_class_total.get(d_v, 0) + 1
        if e_v == d_v:
            overall_correct += 1
            per_class_correct[d_v] = per_class_correct.get(d_v, 0) + 1

    return JudgeDAgreementStats(
        case_count=n,
        overall_match_rate=overall_correct / n,
        per_class_match_rate={
            cls: per_class_correct.get(cls, 0) / per_class_total[cls]
            for cls in per_class_total
        },
    )
