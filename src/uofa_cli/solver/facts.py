"""What a solver artifact says, quoted back with the bytes it came from.

Three record types, kept apart because they support different claims.

**SolverFact** -- a value read out of an artifact. `Ti6Al4V_Base_BISO`'s
Young's modulus is 108222.363244 MPa because `EngineeringData.xml` says so, and
the fact carries the literal text that said it. The value is certain; it was
read, not inferred. The *binding* -- which material is "the rod" -- is a
separate question with its own confidence, because a materials library holds
unused and superseded entries and nothing in the file says which one the
published run used.

**SolverCaution** -- a message the solver or its environment reported. These are
NOT weakeners and must never be called that anywhere a reader can see: a
weakener is a catalog rule with an id, and these have no rule behind them. They
are cautions the solver itself raised, surfaced as evidence for a human to
adjudicate. `severity` carries the solver's own word, not our reading of it.

**AbsentArtifact** -- something the package states is missing. The strongest
completeness evidence in the OSF folder is Workbench's own record that the
archive was written without solution files, listing `ds.dat`, `file.rst` and
`solve.out` by name. A package that testifies to its own gaps is worth more
than one we merely failed to find things in, so the two are never conflated:
`stated_by` says who made the claim.

Nothing here judges. No record has a pass/fail field, and none may grow one --
statuses are proposed by extraction and settled by a human, and stamped
`statusProvenance` when they are (excel_mapper.py:487-492).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Confidence that a fact is bound to the thing the reader thinks it is bound to.
# Not the confidence that the value was read correctly -- that is 1.0 by
# construction, which is exactly what makes these different from prose routes.
CERTAIN = 1.0
LIBRARY_ENTRY = 0.5   # present in the library; nothing says the run used it

# Solver artifacts whose absence a reader is actually looking for. Used only to
# order a readout -- never to filter one.
SOLVER_ARTIFACTS = frozenset({
    "ds.dat", "solve.out", "file.rst", "file0.rst", "file.rth", "file.mntr",
    "file0.err", "file.err", "file.gst", "file.db", "matml.xml",
})


@dataclass(frozen=True)
class SolverFact:
    """One value, and the bytes it was read from."""
    key: str
    value: object
    units: str = ""
    scope: str = ""
    source_member: str = ""
    source_locator: str = ""
    source_text: str = ""
    binding_confidence: float = CERTAIN

    def as_dict(self) -> dict:
        out = {"key": self.key, "value": self.value}
        if self.units:
            out["units"] = self.units
        if self.scope:
            out["scope"] = self.scope
        out["sourceMember"] = self.source_member
        if self.source_locator:
            out["sourceLocator"] = self.source_locator
        if self.source_text:
            out["sourceText"] = self.source_text
        out["bindingConfidence"] = self.binding_confidence
        return out


@dataclass(frozen=True)
class SolverCaution:
    """A message the solver reported. Not a weakener; not a finding of ours."""
    severity: str          # the solver's own word: information | warning | error
    summary: str
    detail: str = ""
    reported_at: str = ""
    source_member: str = ""

    def as_dict(self) -> dict:
        out = {"severity": self.severity, "summary": self.summary}
        if self.detail:
            out["detail"] = self.detail
        if self.reported_at:
            out["reportedAt"] = self.reported_at
        out["sourceMember"] = self.source_member
        return out


@dataclass(frozen=True)
class AbsentArtifact:
    """Something the evidence package says is not in it."""
    name: str
    location: str = ""     # redacted directory token
    stated_by: str = ""    # who says so, e.g. "workbench-archive-record"
    source_member: str = ""

    def as_dict(self) -> dict:
        out = {"name": self.name}
        if self.location:
            out["location"] = self.location
        out["statedBy"] = self.stated_by
        out["sourceMember"] = self.source_member
        return out


@dataclass
class SolverEvidence:
    """Everything read out of one evidence folder's solver artifacts."""
    facts: list[SolverFact] = field(default_factory=list)
    cautions: list[SolverCaution] = field(default_factory=list)
    absent: list[AbsentArtifact] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)
    redaction_summary: str = ""

    def extend(self, other: "SolverEvidence") -> None:
        self.facts.extend(other.facts)
        self.cautions.extend(other.cautions)
        self.absent.extend(other.absent)
        self.unparsed.extend(other.unparsed)

    def by_key(self, key: str) -> list[SolverFact]:
        return [f for f in self.facts if f.key == key]

    def distinct_facts(self) -> dict[tuple, list[SolverFact]]:
        """Group identical readings, keyed by (key, scope, value, units).

        One Workbench archive carries eleven materials libraries -- one per
        system -- and they overlap heavily, so a flat list repeats the same
        value ten times and buries the thing worth seeing. Grouping keeps every
        source (two systems agreeing is corroboration, and the members are
        named) while letting a reader see at a glance where two systems DISAGREE
        about the same material.

        Values are grouped as read. Two readings in different units are not
        merged, because deciding they are equal requires a conversion this
        layer deliberately does not perform.
        """
        out: dict[tuple, list[SolverFact]] = {}
        for f in self.facts:
            out.setdefault((f.key, f.scope, f.value, f.units), []).append(f)
        return out

    def disagreements(self) -> dict[tuple[str, str], list[tuple]]:
        """Where one (key, scope) has more than one distinct reading.

        Reported, never resolved. A library holding three different Young's
        moduli for titanium is a fact about the library; which one is right is
        not this layer's call.
        """
        seen: dict[tuple[str, str], set] = {}
        for f in self.facts:
            seen.setdefault((f.key, f.scope), set()).add((f.value, f.units))
        return {k: sorted(v, key=repr) for k, v in seen.items() if len(v) > 1}

    def cautions_by_severity(self, severity: str) -> list[SolverCaution]:
        return [c for c in self.cautions if c.severity == severity]

    @property
    def severity_counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.cautions:
            out[c.severity] = out.get(c.severity, 0) + 1
        return out

    def as_dict(self) -> dict:
        return {
            "solverFact": [f.as_dict() for f in self.facts],
            "solverCaution": [c.as_dict() for c in self.cautions],
            "absentArtifact": [a.as_dict() for a in self.absent],
            "unparsed": list(self.unparsed),
        }

    def summarise(self) -> list[str]:
        """Readout lines. States what could not be parsed, not only what could."""
        lines = [f"{len(self.facts)} fact(s) read from solver artifacts"]
        if self.cautions:
            counts = self.severity_counts
            detail = ", ".join(f"{n} {sev}" for sev, n in sorted(counts.items()))
            lines.append(f"{len(self.cautions)} solver-reported caution(s): {detail}")
        if self.absent:
            names = sorted({a.name for a in self.absent})
            # Order for the reader, do not filter: a stripped `solve.out` and a
            # stripped temp cleanup script are both true, and only one of them
            # is why anyone is looking. Ranking is presentation; dropping the
            # rest would be a judgement this layer is not entitled to make.
            ranked = ([n for n in names if n.lower() in SOLVER_ARTIFACTS]
                      + [n for n in names if n.lower() not in SOLVER_ARTIFACTS])
            shown = ", ".join(ranked[:6]) + (" …" if len(ranked) > 6 else "")
            lines.append(
                f"{len(self.absent)} artifact(s) the package states are absent: {shown}")
        if self.unparsed:
            lines.append(f"{len(self.unparsed)} record(s) could not be parsed "
                         f"and were left unread")
        if self.redaction_summary:
            lines.append(self.redaction_summary)
        return lines
