"""Reviewer render protocol: derive one ReviewerState, enforce invariants.

The reviewer view used to let each panel (at-a-glance, factor table, concerns,
missing-line) read the raw analysis payload on its own, so they drifted out of
agreement and shipped contradictory pages. This module is the fix: a single
pure derivation that every panel reads from, plus an invariant set that makes a
self-contradictory state impossible to construct silently.

No engine/schema/extraction change: this only constrains how the existing
payload is READ. Pure data, framework-free, no HTML.

Reconciliation policy (chosen for a public demo): the live render must always
produce an honest page rather than raise. So `build_reviewer_state` derives a
state that satisfies every invariant by construction - in particular it demotes
any factor an open High/Moderate weakener targets (it cannot read "Evidenced"),
and it never claims "all required accounted for" while a High concern is open.
`assert_reviewer_invariants` still raises `ReviewerInvariantError` on a
hand-constructed bad state, so the guard is real and tested; the builder simply
never emits one.

Known engine-data gap (flagged, out of scope here): almost every High/Critical
weakener targets validation-result or COU nodes, not credibility factors, so its
`factors[]` is empty and it cannot demote a specific factor. When extraction
also over-marks factors as assessed, factor-completeness and the concern list
describe different axes with no payload link between them. We reconcile that by
framing (completeness is a factor metric; "review-ready" additionally requires
no open High concern), not by inventing a factor link.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from space.gloss import gloss_for
from space.summary import expected_factors


class Status(str, Enum):
    EVIDENCED = "Evidenced"
    NOT_STATED = "Not stated"
    NOT_APPLICABLE = "Not applicable"


# One severity vocabulary, shared by the at-a-glance counts and the concern
# lines, so the same item never reads "Medium" in one place and "Moderate" in
# another. "Moderate" is the reader-facing word for the raw "Medium" key.
_SEV_LABEL = {"Critical": "Critical", "High": "High", "Medium": "Moderate", "Low": "Low"}
_SEV_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

# Severities that demote an otherwise-evidenced factor and block the
# "all required accounted for" claim. (Moderate == the raw "Medium" key.)
_DEMOTING = {"Critical", "High", "Medium"}
# "High weakener" for the invariants includes Critical (a strictly worse High).
_HIGH = {"Critical", "High"}


def sev_label(sev) -> str:
    return _SEV_LABEL.get(sev, sev or "")


def sev_rank(sev) -> int:
    return _SEV_RANK.get(sev, 9)


class ReviewerInvariantError(AssertionError):
    """A ReviewerState violated a frozen invariant. Carries the invariant number
    and the offending values so a contradictory page is never silently emitted."""

    def __init__(self, number: int, message: str):
        self.number = number
        super().__init__(f"reviewer invariant {number}: {message}")


@dataclass(frozen=True)
class Concern:
    pattern_id: str
    severity: str          # raw key: Critical / High / Medium / Low
    label: str             # reader-facing word (Medium -> Moderate)
    description: str
    factors: tuple[str, ...]
    hits: int

    @property
    def is_high(self) -> bool:
        return self.severity in _HIGH


@dataclass(frozen=True)
class FactorState:
    name: str
    plain_name: str
    what_it_means: str
    status: Status
    required: bool
    targeting_weakeners: tuple[str, ...]   # pattern ids whose factors[] include this factor


@dataclass(frozen=True)
class ReviewerState:
    cou_name: str
    cou_description: str
    standard: str
    risk_level: object          # int | None
    device_class: object        # str | None
    factors: tuple[FactorState, ...]
    n_evidenced: int
    n_expected: int
    n_required: int
    completeness_pct: int        # derived: evidenced / expected
    required_all_accounted: bool
    open_high_count: int         # open Critical + High concerns
    missing: tuple[str, ...]     # required factors that are not Evidenced
    concerns: tuple[Concern, ...]
    severity_counts: dict        # raw severity key -> count, single source for at-a-glance
    gates: dict
    authenticity: dict

    @property
    def has_high_weakener(self) -> bool:
        return self.open_high_count > 0


def _build_concerns(weakeners: list[dict]) -> tuple[Concern, ...]:
    out = []
    for w in weakeners or []:
        sev = w.get("severity")
        out.append(Concern(
            pattern_id=w.get("patternId") or w.get("pattern_id") or "",
            severity=sev,
            label=sev_label(sev),
            description=(w.get("description") or "").strip(),
            factors=tuple(w.get("factors") or []),
            hits=w.get("hits") if isinstance(w.get("hits"), int) else 1,
        ))
    out.sort(key=lambda c: (sev_rank(c.severity), c.pattern_id))
    return tuple(out)


def build_reviewer_state(analysis: dict, gloss: dict | None = None) -> ReviewerState:
    """Derive the single source of truth for the reviewer view from the payload.

    Status precedence (per factor, evaluated in order):
      1. scoped out for this COU/risk level         -> NOT_APPLICABLE
      2. targeted by an open High/Moderate weakener  -> NOT_STATED  (cannot be Evidenced)
      3. explicit positive evidence (assessed)       -> EVIDENCED
      4. otherwise                                   -> NOT_STATED
    Absence never yields EVIDENCED; that is the rule that kills the Build B regression.
    """
    ctx = analysis.get("context", {}) or {}
    pack = analysis.get("pack", "vv40")
    c = analysis.get("completeness", {}) or {}
    expected = expected_factors(pack)

    concerns = _build_concerns(analysis.get("weakeners", []) or [])

    # factor name -> pattern ids of demoting (High/Moderate) concerns that target it
    targeting: dict[str, list[str]] = {}
    for conc in concerns:
        if conc.severity in _DEMOTING:
            for fac in conc.factors:
                targeting.setdefault(fac, []).append(conc.pattern_id)

    assessed = set(c.get("assessed") or [])
    excluded = set(c.get("excluded") or [])

    factors: list[FactorState] = []
    for name in expected:
        g = gloss_for(name, gloss)
        targeted = tuple(targeting.get(name, ()))
        if name in excluded:
            status = Status.NOT_APPLICABLE
        elif targeted:
            status = Status.NOT_STATED       # demoted: a High/Moderate concern disputes it
        elif name in assessed:
            status = Status.EVIDENCED
        else:
            status = Status.NOT_STATED
        factors.append(FactorState(
            name=name,
            plain_name=g.get("plain_name", name),
            what_it_means=g.get("what_it_means", ""),
            status=status,
            required=name not in excluded,   # in-scope == required at this risk level
            targeting_weakeners=targeted,
        ))

    n_evidenced = sum(1 for f in factors if f.status is Status.EVIDENCED)
    n_expected = len(expected)
    n_required = sum(1 for f in factors if f.required)
    completeness_pct = round(100 * n_evidenced / n_expected) if n_expected else 0
    open_high_count = sum(1 for conc in concerns if conc.is_high)

    # Required factors still lacking evidence drive the "what is still missing"
    # section. Same source the completeness gate uses.
    missing = tuple(f.name for f in factors if f.required and f.status is not Status.EVIDENCED)

    # "all required accounted for" is true ONLY if every required factor is
    # Evidenced AND no High/Critical concern is open. This is the reframing that
    # makes "100% factors evidenced" and "High concerns open" coexist honestly.
    required_all_accounted = (not missing) and (open_high_count == 0)

    severity_counts: dict[str, int] = {}
    for conc in concerns:
        severity_counts[conc.severity] = severity_counts.get(conc.severity, 0) + 1

    structural_ok = bool(analysis.get("structural", {}).get("conforms"))
    completeness_ok = not missing
    gates = {
        "structural": structural_ok,
        "completeness": completeness_ok,
        "passed": int(structural_ok) + int(completeness_ok),
        "total": 2,
    }

    return ReviewerState(
        cou_name=ctx.get("cou_name") or "Not stated",
        cou_description=(ctx.get("cou_description") or "").strip(),
        standard=ctx.get("standard") or ctx.get("pack") or "Not stated",
        risk_level=ctx.get("model_risk_level"),
        device_class=ctx.get("device_class"),
        factors=tuple(factors),
        n_evidenced=n_evidenced,
        n_expected=n_expected,
        n_required=n_required,
        completeness_pct=completeness_pct,
        required_all_accounted=required_all_accounted,
        open_high_count=open_high_count,
        missing=missing,
        concerns=concerns,
        severity_counts=severity_counts,
        gates=gates,
        authenticity=ctx.get("authenticity", {}) or {},
    )


def assert_reviewer_invariants(state: ReviewerState) -> None:
    """Validate the frozen invariant set before any HTML exists. Raises
    ReviewerInvariantError on the first violation. build_reviewer_state satisfies
    all of these by construction; this guards against a future code path (or a
    hand-built state) that does not."""
    by_name = {f.name: f for f in state.factors}

    # 1: no EVIDENCED factor is the target of an open High/Moderate weakener.
    for conc in state.concerns:
        if conc.severity not in _DEMOTING:
            continue
        for fac in conc.factors:
            f = by_name.get(fac)
            if f is not None and f.status is Status.EVIDENCED:
                raise ReviewerInvariantError(
                    1, f"factor {fac!r} is EVIDENCED but targeted by {conc.pattern_id} [{conc.severity}]")

    # 2: cannot claim everything accounted for while a High/Critical concern is open.
    if state.required_all_accounted and state.has_high_weakener:
        raise ReviewerInvariantError(
            2, f"required_all_accounted with {state.open_high_count} open High concern(s)")

    # 3: at-a-glance evidenced count equals the EVIDENCED rows in the table.
    actual = sum(1 for f in state.factors if f.status is Status.EVIDENCED)
    if state.n_evidenced != actual:
        raise ReviewerInvariantError(3, f"n_evidenced={state.n_evidenced} but {actual} EVIDENCED rows")

    # 4: the severity words in severity_counts match the words on concern lines.
    glance_words = {sev_label(s) for s in state.severity_counts}
    line_words = {conc.label for conc in state.concerns}
    if glance_words != line_words:
        raise ReviewerInvariantError(4, f"severity words glance={glance_words} lines={line_words}")

    # 5: required_all_accounted only if every required factor is Evidenced or N/A.
    if state.required_all_accounted:
        bad = [f.name for f in state.factors
               if f.required and f.status not in (Status.EVIDENCED, Status.NOT_APPLICABLE)]
        if bad:
            raise ReviewerInvariantError(5, f"required_all_accounted but unaccounted: {bad}")

    # 6: at-a-glance concern count equals the number of concern lines.
    if sum(state.severity_counts.values()) != len(state.concerns):
        raise ReviewerInvariantError(
            6, f"severity_counts total {sum(state.severity_counts.values())} != {len(state.concerns)} concerns")
