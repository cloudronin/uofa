"""Render solver artifacts as text for the extraction corpus.

Registered in `document_reader._READERS` for the Workbench formats. What it
emits is a *digest* of what `solver.reader` read, not the artifacts themselves:
a project file is 233 KB of XML that is 95% storage plumbing, and putting that
in front of an extractor spends the budget on nothing and ships operator paths
off the machine.

Everything here is redacted upstream by `solver.reader`. The assertion at the
end is a boundary check, not a routine one -- this is the last point before
text leaves for a language model.
"""

from __future__ import annotations

from pathlib import Path

from uofa_cli.document_reader import DocumentChunk
from uofa_cli.solver import redact
from uofa_cli.solver.facts import SOLVER_ARTIFACTS, SolverEvidence
from uofa_cli.solver.reader import read_evidence

FORMAT = "ansys"

# Cautions are quoted in full up to this many; beyond it the tail is counted.
# 78 in one real project, and the long tail repeats.
_MAX_CAUTIONS = 40

# Inherently dimensionless. Annotating these "(no unit declared)" is noise --
# there is no unit to declare, and the annotation exists to warn about a
# quantity whose scale is unknown.
_DIMENSIONLESS = {"poissons ratio", "hardening points"}


def read_ansys(path: Path) -> list[DocumentChunk]:
    """Read one Workbench artifact or archive into corpus chunks."""
    evidence = read_evidence(path)
    sections = [
        ("Solver project and software", _project_section(evidence)),
        ("Materials defined in the project", _materials_section(evidence)),
        ("Cautions reported by the solver", _cautions_section(evidence)),
        ("Artifacts the package states are absent", _absent_section(evidence)),
    ]
    chunks = []
    for heading, body in sections:
        if not body:
            continue
        text = f"## {heading}\n\n{body}\n"
        assert redact.looks_redacted(text), (
            f"unredacted operator path in the {heading!r} section — "
            "solver.reader must redact before this point")
        chunks.append(DocumentChunk(
            text=text, source_file=path.name, source_path=str(path),
            section_heading=heading, format=FORMAT))
    return chunks


def _project_section(ev: SolverEvidence) -> str:
    rows = [f"- {f.key.split('.', 1)[1].replace('_', ' ')}: {f.value}"
            for f in ev.facts
            if f.key.startswith("project.") and f.key != "project.addin"]
    addins = ev.by_key("project.addin")
    if addins:
        named = ", ".join(f"{a.value} {a.scope}".strip() for a in addins[:12])
        rows.append(f"- addins loaded ({len(addins)}): {named}")
    schema = ev.by_key("materials.schema_version")
    if schema:
        rows.append(f"- materials library schema: {schema[0].value}")
    return "\n".join(rows)


def _materials_section(ev: SolverEvidence) -> str:
    """One block per material, distinct readings only, grouped by declared unit.

    Units are never converted here. The library really does mix them: the same
    rod is 170554.2548 MPa in `EngineeringData.xml` and 170554254800 with no
    declared unit in a per-system `.engd`. Those are almost certainly the same
    number, but "almost certainly" is a conversion, and a silent conversion that
    is wrong produces an answer that validates -- the exact failure the
    requirement layer's open question Q3 is about.

    So disagreement is only ever reported WITHIN one declared unit. Across
    units the readings are listed side by side and called what they are: not
    comparable without a stated conversion.
    """
    grouped: dict[str, dict[str, dict[str, list]]] = {}
    for (key, scope, value, units), sources in ev.distinct_facts().items():
        if not key.startswith("material."):
            continue
        label = key.split(".", 1)[1].replace("_", " ")
        grouped.setdefault(scope, {}).setdefault(label, {}).setdefault(
            units, []).append(value)
    if not grouped:
        return ""

    rows = []
    for material in sorted(grouped):
        rows.append(f"- {material}")
        for label in sorted(grouped[material]):
            by_unit = grouped[material][label]
            parts = []
            conflicted = False
            for units in sorted(by_unit):
                values = sorted(by_unit[units], key=repr)
                if len(values) > 1:
                    conflicted = True
                shown = " / ".join(str(v) for v in values)
                if units:
                    parts.append(f"{shown} {units}")
                elif label in _DIMENSIONLESS:
                    parts.append(shown)
                else:
                    parts.append(f"{shown} (no unit declared)")
            note = ""
            if conflicted:
                note = "  <- systems disagree within one unit"
            elif len(by_unit) > 1 and label not in _DIMENSIONLESS:
                note = "  <- also recorded without a declared unit; not " \
                       "comparable without a stated conversion"
            rows.append(f"    {label}: {'; '.join(parts)}{note}")

    rows.append(
        f"\n({len(grouped)} material(s) across the project's libraries. A "
        "library may hold unused, superseded or duplicate entries; the file "
        "does not say which one a published run used. Where a property has "
        "more than one reading, all are shown and none is preferred.)")
    return "\n".join(rows)


def _cautions_section(ev: SolverEvidence) -> str:
    """Messages the solver itself raised.

    Deliberately NOT called weaknesses, defects or weakeners. A weakener is a
    catalog rule with an id, and nothing here has one — these are the solver's
    own words, carried through for a human to weigh.
    """
    if not ev.cautions:
        return ""
    counts = ", ".join(f"{n} {sev}" for sev, n in sorted(ev.severity_counts.items()))
    rows = [f"The solver recorded {len(ev.cautions)} message(s) ({counts}). "
            f"These are the solver's own reports, not findings of this tool.", ""]
    seen: set[str] = set()
    shown = 0
    for caution in ev.cautions:
        if caution.summary in seen:
            continue
        seen.add(caution.summary)
        if shown >= _MAX_CAUTIONS:
            break
        stamp = f" [{caution.reported_at}]" if caution.reported_at else ""
        rows.append(f"- {caution.severity.upper()}{stamp}: {caution.summary}")
        shown += 1
    remaining = len(seen) - shown
    if remaining > 0:
        rows.append(f"- … and {remaining} further distinct message(s), "
                    f"not quoted here")
    return "\n".join(rows)


def _absent_section(ev: SolverEvidence) -> str:
    if not ev.absent:
        return ""
    names = sorted({a.name for a in ev.absent})
    # Rank, do not filter. A stripped `solve.out` and a stripped temp cleanup
    # script are equally true and only one is why anyone is reading; alphabetical
    # order buries it behind sixty `cleanup-ansys-*.bat`. Dropping the rest would
    # be a judgement this layer is not entitled to make.
    solver = [n for n in names if n.lower() in SOLVER_ARTIFACTS]
    other = [n for n in names if n.lower() not in SOLVER_ARTIFACTS]
    stated_by = sorted({a.stated_by for a in ev.absent})
    rows = [f"The package's own records state that {len(names)} file(s) are "
            f"not present (recorded by: {', '.join(stated_by)}):", ""]
    if solver:
        rows.append("Solver inputs, logs and results:")
        rows += [f"- {name}" for name in solver]
        rows.append("")
        rows.append("Other files named in the same record:")
    rows += [f"- {name}" for name in other[:40]]
    if len(other) > 40:
        rows.append(f"- … and {len(other) - 40} more")
    return "\n".join(rows)
