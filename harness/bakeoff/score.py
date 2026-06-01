"""Bakeoff scorecard — the Gate's §3.2 metric, re-pointable to disposition.

Applies a per-row answer key to a model's structured answer and computes the
metric components + the headline **selective risk-coverage**. The same machinery
scores the **explanation** task (P0) and the **disposition** task (the addendum's
disposition gate): both reduce to scoring a selected §5B action class + a
calibrated confidence against the row's key.

Read every result on the **hard-core strata**, not just the aggregate (the
false-positive-kill guard, addendum): an aggregate pass that masks hard-cell
failure means the *slice* is too easy, not that the task is commodity.

Confidence elicitation is **verbalized** — the model states a confidence
label/score in its structured output. Fixed here so the selective curve is
reproducible and the stock-vs-target comparison is apples-to-apples (the SLM
spec §3.2 elicitation-matching rule; for this single-model gate, fixing
verbalized is sufficient).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# §5B action vocabulary tagged by posture, so a *false-OK* (proceeding when the
# gold action blocks) is flagged as the headline-dangerous **harmful** bucket —
# the error a regulated submission cannot tolerate (§3.2).
BLOCK_CLASSES = frozenset({"supply-evidence", "acquire-validation", "restrict-cou", "reject"})
PROCEED_CLASSES = frozenset({"accept-residual-risk", "accept", "none"})

_CONF_LABEL = {"high": 0.9, "medium": 0.6, "moderate": 0.6, "low": 0.3, "very-low": 0.1}


def confidence_to_float(conf) -> float:
    """Normalize a verbalized confidence (label or 0–1 number) to a float."""
    if isinstance(conf, bool):
        return 0.5
    if isinstance(conf, (int, float)):
        return max(0.0, min(1.0, float(conf)))
    if isinstance(conf, str):
        s = conf.strip().lower()
        if s in _CONF_LABEL:
            return _CONF_LABEL[s]
        try:
            return max(0.0, min(1.0, float(s)))
        except ValueError:
            return 0.5
    return 0.5


def bucket_action(selected: str | None, gold_action: dict) -> str:
    """Bucket the selected §5B class vs the gold: correct / partial / wrong / harmful.

    - ``correct``  — matches the adjudicated-best class.
    - ``partial``  — a *coherent alternative* but not the adjudicated-best (on the
      multi-coherent §5B rows this is where tacit which-fix-when knowledge shows).
    - ``harmful``  — the dangerous error: proceeds when the gold action blocks
      (false-OK on a case that needs action).
    - ``wrong``    — any other mismatch.
    """
    gold = gold_action.get("selected_class")
    alternatives = set(gold_action.get("coherent_alternatives", []))
    if selected == gold:
        return "correct"
    if selected in alternatives:
        return "partial"
    if gold in BLOCK_CLASSES and selected in PROCEED_CLASSES:
        return "harmful"
    return "wrong"


@dataclass
class RowScore:
    row_id: str
    hard_core: bool
    action_bucket: str            # correct | partial | wrong | harmful
    forbidden_violated: bool      # a §7.6 honest-promise / measure-don't-judge breach
    confidence: float             # verbalized → float
    confidence_acceptable: bool
    escalated: bool
    # "handled correctly" for the selective curve: right action + no forbidden claim.
    correct: bool = field(init=False)

    def __post_init__(self):
        self.correct = (self.action_bucket == "correct") and (not self.forbidden_violated)


def _confidence_acceptable(conf: float, acceptable) -> bool:
    """Is the verbalized confidence inside the row's acceptable range?

    Each entry is a numeric range ``"0.80-0.95"`` or a label ``"high"`` (matched
    by proximity). No constraint → accept.
    """
    if not acceptable:
        return True
    for entry in acceptable:
        s = str(entry).strip().lower()
        parts = s.split("-")
        if len(parts) == 2:                       # numeric range "lo-hi"
            try:
                lo, hi = float(parts[0]), float(parts[1])
                if lo <= conf <= hi:
                    return True
                continue
            except ValueError:
                pass                              # not numeric (e.g. "very-low") → label path
        if s in _CONF_LABEL and abs(_CONF_LABEL[s] - conf) < 0.16:
            return True
    return False


def score_row(row: dict, answer: dict) -> RowScore:
    """Apply ``row['answer_key']`` to a model ``answer``.

    ``answer`` is the normalized model output:
    ``{action_class, confidence, escalate, forbidden_violated?}`` — the runner
    extracts ``action_class`` (constrained decoding / judge) and the verbalized
    ``confidence``; ``forbidden_violated`` is an optional pre-judged flag
    (default False — the deterministic action + calibration metrics stand alone).
    """
    key = row.get("answer_key", {})
    gold_action = key.get("gold_action", {})
    conf = confidence_to_float(answer.get("confidence"))
    return RowScore(
        row_id=row.get("row_id", "?"),
        hard_core=bool(row.get("hard_core", row.get("split", "").startswith("train:hard"))),
        action_bucket=bucket_action(answer.get("action_class"), gold_action),
        forbidden_violated=bool(answer.get("forbidden_violated", False)),
        confidence=conf,
        confidence_acceptable=_confidence_acceptable(conf, key.get("acceptable_confidence")),
        escalated=bool(answer.get("escalate", False)),
    )


# ── Aggregate metrics ────────────────────────────────────────────────────────


def selective_points(scores: list[RowScore]) -> list[dict]:
    """The selective risk-coverage curve: at each confidence threshold τ, the
    (coverage, risk) over the *handled* set (not escalated, confidence ≥ τ)."""
    if not scores:
        return []
    thresholds = sorted({s.confidence for s in scores}, reverse=True)
    n = len(scores)
    points = []
    for tau in thresholds:
        handled = [s for s in scores if not s.escalated and s.confidence >= tau]
        if not handled:
            continue
        errors = sum(1 for s in handled if not s.correct)
        points.append({"tau": tau, "coverage": len(handled) / n, "risk": errors / len(handled)})
    return points


def coverage_at_risk(points: list[dict], alpha: float) -> float:
    """Max coverage achievable with risk ≤ α — the headline decision metric."""
    return max((p["coverage"] for p in points if p["risk"] <= alpha), default=0.0)


def ece(scores: list[RowScore], bins: int = 10) -> float:
    """Expected calibration error over verbalized confidence (lower is better)."""
    considered = [s for s in scores if not s.escalated]
    if not considered:
        return 0.0
    total = len(considered)
    err = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [s for s in considered if (lo < s.confidence <= hi) or (b == 0 and s.confidence == 0.0)]
        if not bucket:
            continue
        acc = sum(1 for s in bucket if s.correct) / len(bucket)
        conf = sum(s.confidence for s in bucket) / len(bucket)
        err += (len(bucket) / total) * abs(acc - conf)
    return err


def summarize(scores: list[RowScore], *, alpha: float = 0.02) -> dict:
    """Aggregate the §3.2 components for a set of row scores."""
    n = len(scores)
    if n == 0:
        return {"n": 0}
    buckets = {b: sum(1 for s in scores if s.action_bucket == b)
               for b in ("correct", "partial", "wrong", "harmful")}
    points = selective_points(scores)
    return {
        "n": n,
        "action_buckets": buckets,
        "dangerous_error_rate": buckets["harmful"] / n,          # the headline safety axis
        "forbidden_violation_rate": sum(1 for s in scores if s.forbidden_violated) / n,
        "escalation_rate": sum(1 for s in scores if s.escalated) / n,
        "ece": ece(scores),
        "selective_coverage_at_alpha": coverage_at_risk(points, alpha),
        "alpha": alpha,
        "selective_curve": points,
    }


def scorecard(rows: list[dict], answers: list[dict], *, alpha: float = 0.02) -> dict:
    """Full Gate scorecard: overall + **hard-core-strata** segmentation.

    The hard-core block is the one that decides the gate — an aggregate pass that
    masks hard-cell failure is a *slice-too-easy* finding, not a commodity one.
    """
    by_id = {a.get("row_id"): a for a in answers}
    scores = [score_row(r, by_id.get(r.get("row_id"), {})) for r in rows]
    hard = [s for s in scores if s.hard_core]
    return {
        "alpha": alpha,
        "overall": summarize(scores, alpha=alpha),
        "hard_core": summarize(hard, alpha=alpha),
        "elicitation": "verbalized",
    }


def gate_read(card: dict, *, max_dangerous_error: float = 0.0,
              min_selective_coverage: float = 0.5, min_hard_core_n: int = 20) -> dict:
    """Read the gate on the **hard-core strata** against absolute bars.

    Returns whether the stock model clears (dangerous-error ≤ bar AND selective
    coverage at α ≥ bar) — but **a clear is not a verdict below ``min_hard_core_n``
    hard cells.** At small N a clear is far more likely "slice too easy" than
    "task commodity" (the addendum's false-positive-kill guard), so it routes to
    *grow-the-slice-and-rerun*, never to "explanation commodity → escalate to
    disposition." A fail is more informative than a clear at any size. The caller
    drives the ladder + disposition routing.
    """
    hc = card.get("hard_core", {})
    n = hc.get("n", 0)
    if not n:
        return {"clears": False, "preview": True,
                "recommended_next": "rebuild the hard-core cells (slice underpowered)",
                "note": "no hard-core rows"}
    clears = (hc["dangerous_error_rate"] <= max_dangerous_error
              and hc["selective_coverage_at_alpha"] >= min_selective_coverage)
    preview = n < min_hard_core_n
    if preview:
        recommended_next = (f"grow the hard-core slice and rerun — a clear at n={n} is more likely "
                            "slice-too-easy than commodity" if clears else
                            f"diagnose the failing hard cells (n={n}), then grow the slice")
        note = (f"PREVIEW (hard-core n={n} < {min_hard_core_n}) — NOT a gate verdict. "
                + ("Distrust this clear; it routes to grow-and-rerun, not to the disposition gate."
                   if clears else "A fail is informative even at this size."))
    else:
        recommended_next = ("run the disposition gate (explanation commodity at ship size; the moat is "
                            "one level up)" if clears else
                            "escalate to stock 7–8B before any fine-tune (main-plan ladder)")
        note = ("clears on hard-core → explanation commodity at this size; route per the decision tree"
                if clears else
                "fails on hard-core → escalate to stock 7–8B, then corpus-justified if it also fails")
    return {
        "clears": clears,
        "preview": preview,
        "recommended_next": recommended_next,
        "hard_core_n": n,
        "dangerous_error_rate": hc["dangerous_error_rate"],
        "selective_coverage_at_alpha": hc["selective_coverage_at_alpha"],
        "bars": {"max_dangerous_error": max_dangerous_error, "min_selective_coverage": min_selective_coverage},
        "note": note,
    }
