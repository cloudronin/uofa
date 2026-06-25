"""Credibility report: one derived state, enforced invariants — shared by the
CLI `report` command and the demo Space reviewer view.

Two layers, both pack-neutral and framework-free (pure data, no HTML, no Gradio):

  1. `compute_findings(pack, factor_statuses, shacl, firings)` assembles the
     analysis payload — completeness (owned here, derived from confirmed factor
     statuses), weakeners (enriched with their factor focus via
     `uofa_cli.weakener_focus`), and structural SHACL findings. No
     Accepted/Not-Accepted headline: that verdict is a human act, deferred.

  2. `build_report_state(analysis, gloss)` derives the single `ReportState` every
     consumer reads, and `assert_report_invariants(state)` validates the frozen
     invariant set before any rendering. The builder satisfies every invariant by
     construction (it demotes any factor an open High/Moderate weakener targets,
     and never claims "all required accounted for" while a High concern is open),
     so a self-contradictory report cannot be silently produced.

The status-derivation precedence (per factor, in order):
  1. scoped out for this COU/risk level         -> NOT_APPLICABLE
  2. targeted by an open High/Moderate weakener  -> NOT_STATED  (cannot be Evidenced)
  3. explicit positive evidence (assessed)       -> EVIDENCED
  4. otherwise                                   -> NOT_STATED
Absence never yields EVIDENCED — the rule that keeps a "100% complete" report
from coexisting with High-severity concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from uofa_cli.weakener_focus import enrich_firings, expected_factors

_EXCLUDED_STATUSES = ("scoped-out", "not-applicable")


# ── Layer 1: findings/completeness payload ──────────────────────────────────


def _headline(n_assessed: int, n_expected: int, n_missing: int,
              firings: list[dict], sev_counts: dict[str, int]) -> str:
    # Gap-Finder: lead with the gaps (weakeners, then unassessed), completeness last.
    parts = []
    if firings:
        order = ["Critical", "High", "Medium", "Low"]
        bits = [f"{sev_counts[s]} {s}" for s in order if sev_counts.get(s)]
        breakdown = f" ({', '.join(bits)})" if bits else ""
        parts.append(f"{len(firings)} weakener{'s' if len(firings) != 1 else ''} fired{breakdown}")
    else:
        parts.append("no weakeners fired")
    if n_missing:
        parts.append(f"{n_missing} factor{'s' if n_missing != 1 else ''} not assessed")
    parts.append(f"{n_assessed} of {n_expected} credibility factors assessed")
    return "; ".join(parts) + "."


def compute_findings(pack: str, factor_statuses: dict[str, str], shacl: dict,
                     firings: list[dict]) -> dict:
    """Assemble the analysis payload (completeness + weakeners + structural).

    Args:
        factor_statuses: factor_type -> confirmed status ('assessed' /
            'not-assessed' / 'scoped-out' / 'not-applicable').
        shacl: {"conforms": bool, "violations": [ {path, message, severity}, ... ]}.
        firings: rich firing dicts from `rules.parse_firings_jsonld`.
    """
    expected = expected_factors(pack)
    assessed = [n for n in expected if factor_statuses.get(n) == "assessed"]
    missing = [n for n in expected if factor_statuses.get(n) == "not-assessed"]
    excluded = [n for n in expected if factor_statuses.get(n) in _EXCLUDED_STATUSES]
    denom = len(expected) - len(excluded)

    enriched = enrich_firings(firings, pack)  # attaches factor focus per pack manifests
    sev_counts: dict[str, int] = {}
    for w in enriched:
        sev = w.get("severity", "Medium")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    violations = [
        {"path": v.get("path"), "message": v.get("message"), "severity": v.get("severity")}
        for v in shacl.get("violations", [])
    ]

    return {
        "pack": pack,
        "completeness": {
            "assessed": assessed,
            "missing": missing,
            "excluded": excluded,
            "n_assessed": len(assessed),
            "n_expected": len(expected),
            "denom": denom,
        },
        "weakeners": enriched,
        "weakener_severity": sev_counts,
        "structural": {
            "conforms": shacl.get("conforms"),
            "violations": violations,
            "n": len(violations),
        },
        "headline": _headline(len(assessed), len(expected), len(missing), enriched, sev_counts),
    }


# ── Layer 2: derived state + invariants ─────────────────────────────────────


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


def _gloss_for(name: str, gloss: dict | None) -> dict:
    """factor -> plain-language lookup, with a name fallback so a row never
    renders blank. Decoupled from the Space's gloss module: any dict keyed by
    factor name with {plain_name, what_it_means} works; None yields the raw name."""
    return (gloss or {}).get(name) or {"plain_name": name, "what_it_means": ""}


class ReportInvariantError(AssertionError):
    """A ReportState violated a frozen invariant. Carries the invariant number
    and the offending values so a contradictory report is never silently emitted."""

    def __init__(self, number: int, message: str):
        self.number = number
        super().__init__(f"report invariant {number}: {message}")


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
class ReportState:
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
    # Optional disclosed risk-tier assumption (mrm-nist model cards declare no risk
    # tier, so that profile assesses against an assumed MRL; surfacing it makes
    # W-EP-04 fire against a STATED assumption, not a hidden input). Empty for
    # vv40/nasa, whose risk level is derived from a real context of use.
    risk_assumption: str = ""
    # How the factor statuses were derived, surfaced in the readout so a heuristic
    # scan is never mistaken for the tool's judgment: "" (a vetted bundle off disk),
    # "Curated - ...", "LLM extraction - <backend>/<model>", or
    # "Heuristic - ... approximate". Empty renders no provenance line.
    extraction_provenance: str = ""
    # "present" normally; "none" when the source ships no assessable card, so the
    # readout leads with a no-card notice instead of a hollow all-weakeners page.
    documentation_status: str = "present"

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


def build_report_state(analysis: dict, gloss: dict | None = None) -> ReportState:
    """Derive the single source of truth for the report from the payload.

    Status precedence is documented at module level. Absence never yields
    EVIDENCED; that is the rule that kills the "100% complete + High concerns"
    contradiction."""
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
        g = _gloss_for(name, gloss)
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
    # Evidenced AND no High/Critical concern is open.
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

    return ReportState(
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
        risk_assumption=ctx.get("risk_assumption") or "",
        extraction_provenance=ctx.get("extraction_provenance") or "",
        documentation_status=ctx.get("documentation_status") or "present",
    )


def assert_report_invariants(state: ReportState) -> None:
    """Validate the frozen invariant set before any rendering. Raises
    ReportInvariantError on the first violation. build_report_state satisfies all
    of these by construction; this guards a future code path (or a hand-built
    state) that does not."""
    by_name = {f.name: f for f in state.factors}

    # 1: no EVIDENCED factor is the target of an open High/Moderate weakener.
    for conc in state.concerns:
        if conc.severity not in _DEMOTING:
            continue
        for fac in conc.factors:
            f = by_name.get(fac)
            if f is not None and f.status is Status.EVIDENCED:
                raise ReportInvariantError(
                    1, f"factor {fac!r} is EVIDENCED but targeted by {conc.pattern_id} [{conc.severity}]")

    # 2: cannot claim everything accounted for while a High/Critical concern is open.
    if state.required_all_accounted and state.has_high_weakener:
        raise ReportInvariantError(
            2, f"required_all_accounted with {state.open_high_count} open High concern(s)")

    # 3: at-a-glance evidenced count equals the EVIDENCED rows in the table.
    actual = sum(1 for f in state.factors if f.status is Status.EVIDENCED)
    if state.n_evidenced != actual:
        raise ReportInvariantError(3, f"n_evidenced={state.n_evidenced} but {actual} EVIDENCED rows")

    # 4: the severity words in severity_counts match the words on concern lines.
    glance_words = {sev_label(s) for s in state.severity_counts}
    line_words = {conc.label for conc in state.concerns}
    if glance_words != line_words:
        raise ReportInvariantError(4, f"severity words glance={glance_words} lines={line_words}")

    # 5: required_all_accounted only if every required factor is Evidenced or N/A.
    if state.required_all_accounted:
        bad = [f.name for f in state.factors
               if f.required and f.status not in (Status.EVIDENCED, Status.NOT_APPLICABLE)]
        if bad:
            raise ReportInvariantError(5, f"required_all_accounted but unaccounted: {bad}")

    # 6: at-a-glance concern count equals the number of concern lines.
    if sum(state.severity_counts.values()) != len(state.concerns):
        raise ReportInvariantError(
            6, f"severity_counts total {sum(state.severity_counts.values())} != {len(state.concerns)} concerns")
