"""Inter-judge agreement statistics + author adjudication helpers (spec v1.5 §12).

Computes:
  - Pairwise Cohen's κ (sklearn.metrics.cohen_kappa_score) for each of
    AB / AC / BC; per-pair acceptance target ≥ 0.70 (§8.3, §12.1).
  - Fleiss' κ across all three judges (statsmodels); ensemble target ≥ 0.65.
  - Confusion matrices for each judge pair plus author-vs-each-judge.

The most common bug in Fleiss' κ implementations is feeding raw labels
where statsmodels expects an (n_subjects, n_categories) count matrix.
The `_to_count_matrix` helper handles that reshape.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

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
