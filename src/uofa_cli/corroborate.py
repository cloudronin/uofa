"""Put a claim made in prose next to the value in the solver artifact.

This is the join the abstract's third question needs -- *does the evidence
actually support the claim being made* -- and it is piece 1 of both layer
specs: quantity identity, the declared way of knowing that a requirement, a
model output and a measurement refer to the same quantity.

A solver deck is the strongest source of quantity identity there is. Prose says
"Young's modulus 108,222 MPa" in a table whose column headings are three lines
up; `EngineeringData.xml` says the quantity, the material and the unit in one
place, machine-readably. What it does NOT say is which of nine library entries a
published run used, so a match here is corroboration and not proof, and the row
records that.

Three disciplines, none of them optional:

  * **Units convert only through the pack's declared table.** A unit absent from
    it makes the pair `not-comparable`, never coerced. A silent conversion that
    is wrong produces an answer that validates, which is exactly the failure
    open question Q3 of the requirement layer is about -- and this library has a
    live instance of it, a duplicate titanium entry whose tangent modulus is off
    by 10^6.
  * **A divergence is reported, never adjudicated.** A library legitimately
    carries unused, superseded and duplicate entries, so a value that differs
    from a published table may be an unused entry, a later edit, or a table
    error. Saying which is the reader's call.
  * **No catalog vocabulary.** A row is `diverges`, not a weakener, a defect or
    a violation. Those words name rules with ids and nothing here has one.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.solver.facts import SolverEvidence

AGREES = "agrees"
DIVERGES = "diverges"
NOT_COMPARABLE = "not-comparable"
CLAIM_ONLY = "claim-only"
ARTIFACT_ONLY = "artifact-only"

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Claim:
    """A quantity asserted in prose, with where it was asserted."""
    quantity: str
    value: object
    units: str = ""
    scope: str = ""
    source: str = ""
    aliases: tuple[str, ...] = ()

    def matches(self, fact_scope: str) -> bool:
        """Whether this claim is about the same thing as a fact's scope.

        Normalised comparison, because a paper writes "Ti-6Al-4V ELI" and a
        library writes `Ti6Al4V_Base_BISO`. Aliases are supplied by whoever
        wrote the claim; nothing is inferred from string similarity, which
        would silently bind two different materials.
        """
        candidates = {_norm(self.scope), *(_norm(a) for a in self.aliases)}
        return _norm(fact_scope) in candidates


@dataclass(frozen=True)
class CorroborationRow:
    """One quantity, as claimed and as recorded."""
    quantity: str
    scope: str
    verdict: str
    claim_value: object = None
    claim_units: str = ""
    claim_source: str = ""
    fact_value: object = None
    fact_units: str = ""
    fact_source: str = ""
    detail: str = ""
    binding_confidence: float = 0.0

    def as_dict(self) -> dict:
        out = {"quantity": self.quantity, "scope": self.scope,
               "verdict": self.verdict}
        if self.claim_value is not None:
            out["claimValue"] = self.claim_value
            out["claimUnits"] = self.claim_units
            out["claimSource"] = self.claim_source
        if self.fact_value is not None:
            out["artifactValue"] = self.fact_value
            out["artifactUnits"] = self.fact_units
            out["artifactSource"] = self.fact_source
            out["bindingConfidence"] = self.binding_confidence
        if self.detail:
            out["detail"] = self.detail
        return out


@dataclass
class Corroboration:
    """The whole table, plus what it could not compare and why."""
    rows: list[CorroborationRow] = field(default_factory=list)

    def by_verdict(self, verdict: str) -> list[CorroborationRow]:
        return [r for r in self.rows if r.verdict == verdict]

    @property
    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in self.rows:
            out[row.verdict] = out.get(row.verdict, 0) + 1
        return out

    def as_list(self) -> list[dict]:
        return [r.as_dict() for r in self.rows]

    def summarise(self) -> list[str]:
        if not self.rows:
            return ["no claims supplied — nothing to corroborate"]
        counts = self.counts
        lines = [", ".join(f"{n} {verdict}" for verdict, n in sorted(counts.items()))]
        for row in self.by_verdict(DIVERGES):
            lines.append(
                f"diverges — {row.scope} {row.quantity}: "
                f"prose {row.claim_value} {row.claim_units} vs artifact "
                f"{row.fact_value} {row.fact_units} ({row.claim_source})")
        for row in self.by_verdict(NOT_COMPARABLE):
            lines.append(f"not comparable — {row.scope} {row.quantity}: {row.detail}")
        return lines


def corroborate(claims: list[Claim], evidence: SolverEvidence,
                identity: dict | None = None) -> Corroboration:
    """Join `claims` against `evidence` using the pack's quantity identity.

    Works over DISTINCT readings, not raw facts. One Workbench archive carries
    eleven materials libraries, so a naive join emits the same comparison ten
    times and buries the two rows anyone came to see. Where several members
    agree on a value that is corroboration and the count is reported; where
    they disagree, each distinct reading gets its own row.
    """
    identity = {k: v for k, v in (identity or {}).items()
                if not k.startswith("_")}
    readings = _distinct_readings(evidence)
    out = Corroboration()
    used: set[tuple] = set()

    for claim in claims:
        matched = [(key, reading) for key, reading in readings.items()
                   if key[0] == claim.quantity and claim.matches(key[1])]
        if not matched:
            out.rows.append(CorroborationRow(
                quantity=claim.quantity, scope=claim.scope, verdict=CLAIM_ONLY,
                claim_value=claim.value, claim_units=claim.units,
                claim_source=claim.source,
                detail=_candidates(readings, claim)))
            continue
        for key, reading in matched:
            used.add(key)
            for value, units, members, confidence in reading:
                out.rows.append(_compare(
                    claim, key[1], value, units, members, confidence,
                    identity.get(claim.quantity)))

    for key, reading in readings.items():
        if key in used or key[0] not in identity:
            continue
        for value, units, members, confidence in reading:
            out.rows.append(CorroborationRow(
                quantity=key[0], scope=key[1], verdict=ARTIFACT_ONLY,
                fact_value=value, fact_units=units,
                fact_source=_members(members),
                binding_confidence=confidence,
                detail="present in the artifact; no claim was supplied for it"))
    return out


def _distinct_readings(evidence: SolverEvidence) -> dict[tuple, list[tuple]]:
    """(quantity, scope) -> [(value, units, members, binding_confidence)]."""
    grouped: dict[tuple, dict[tuple, list]] = {}
    confidence: dict[tuple, float] = {}
    for fact in evidence.facts:
        key = (fact.key, fact.scope)
        grouped.setdefault(key, {}).setdefault(
            (fact.value, fact.units), []).append(fact.source_member)
        confidence[key] = fact.binding_confidence
    return {
        key: [(value, units, members, confidence[key])
              for (value, units), members in sorted(values.items(), key=repr)]
        for key, values in grouped.items()
    }


def _members(members: list[str]) -> str:
    """Name the sources, and say how many agreed."""
    unique = sorted(set(members))
    if len(unique) == 1:
        return unique[0]
    return f"{unique[0]} (+{len(unique) - 1} further member(s) agreeing)"


def _compare(claim: Claim, scope: str, value, units: str, members: list[str],
             confidence: float, spec: dict | None) -> CorroborationRow:
    row = dict(
        quantity=claim.quantity, scope=scope,
        claim_value=claim.value, claim_units=claim.units,
        claim_source=claim.source, fact_value=value,
        fact_units=units, fact_source=_members(members),
        binding_confidence=confidence)

    if spec is None:
        return CorroborationRow(
            verdict=NOT_COMPARABLE, **row,
            detail=f"{claim.quantity} has no quantity-identity entry in the "
                   f"active pack, so no conversion or tolerance is declared")

    if spec.get("comparison") == "string":
        same = str(claim.value).strip().lower() == str(value).strip().lower()
        return CorroborationRow(
            verdict=AGREES if same else DIVERGES, **row,
            detail="" if same else "recorded release differs from the one claimed")

    claim_canonical = _to_canonical(claim.value, claim.units, spec)
    fact_canonical = _to_canonical(value, units, spec)
    if claim_canonical is None or fact_canonical is None:
        missing = claim.units if claim_canonical is None else units
        shown = missing or "(none declared)"
        return CorroborationRow(
            verdict=NOT_COMPARABLE, **row,
            detail=f"unit {shown} is not in the declared conversion table for "
                   f"{claim.quantity}; refusing to assume one")

    tolerance = float(spec.get("tolerance", 0.0))
    scale = max(abs(claim_canonical), abs(fact_canonical), 1e-30)
    agrees = abs(claim_canonical - fact_canonical) <= tolerance * scale
    unit = spec.get("canonicalUnit", "")
    return CorroborationRow(
        verdict=AGREES if agrees else DIVERGES, **row,
        detail="" if agrees else
        f"{claim_canonical:g} vs {fact_canonical:g} {unit} "
        f"(tolerance {tolerance:.1%})")


def _to_canonical(value, units: str, spec: dict) -> float | None:
    factors = spec.get("units") or {}
    if units not in factors:
        return None
    try:
        return float(value) * float(factors[units])
    except (TypeError, ValueError):
        return None


def _candidates(readings: dict[tuple, list], claim: Claim) -> str:
    """Name the scopes that DO carry this quantity, so a human can bind it."""
    scopes = sorted({key[1] for key in readings if key[0] == claim.quantity})
    if not scopes:
        return "no artifact records this quantity at all"
    shown = ", ".join(scopes[:8]) + (" …" if len(scopes) > 8 else "")
    return (f"no artifact scope matched {claim.scope!r}; this quantity is "
            f"recorded for: {shown}")


def load_claims(path: Path) -> list[Claim]:
    """Read a claim set: a JSON list, or an object with a `claims` list."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = raw.get("claims", []) if isinstance(raw, dict) else raw
    return [Claim(
        quantity=row["quantity"], value=row["value"],
        units=row.get("units", ""), scope=row.get("scope", ""),
        source=row.get("source", ""),
        aliases=tuple(row.get("aliases", ()))) for row in rows]


def _norm(text: str) -> str:
    return _NON_ALNUM.sub("", (text or "").lower())
