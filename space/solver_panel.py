"""Render what the CLI read out of solver artifacts. Presentation only.

The boundary rule this file lives under is stated three times in the repo, and
the sharpest statement of it is a test: `tests/space/test_emittability.py:93`
drives one import dict through both build paths and fails if the digests
diverge -- *"If this fails, the Space has started emitting something the CLI
would not."* So nothing here computes, interprets or emits anything. It calls
`uofa_cli.solver.reader`, the same code `uofa evidence` calls, and turns the
result into markdown.

Correspondingly this never touches the signed document. The panel is attached
to the display payload after `finalize` has already built and signed the
package, so a rendering change cannot move a hash.

Vocabulary is load-bearing here too. A solver message is a caution the solver
raised, never a weakener -- that word names a catalog rule with an id, and the
Inspector's own weakener section is a few lines further up the same page. Using
it for both would tell a reviewer that a rule fired when none did.
"""

from __future__ import annotations

from pathlib import Path

MAX_CAUTIONS = 8
MAX_ABSENT = 10


def summarise(sources: list[Path]) -> dict | None:
    """Read the uploaded artifacts, or None when none of them is one.

    Returns a plain dict rather than a `SolverEvidence` so the payload stays
    JSON-shaped like everything else the Space carries.
    """
    from uofa_cli.solver.facts import SOLVER_ARTIFACTS
    from uofa_cli.solver.reader import read_evidence

    evidence = None
    for source in sources or []:
        found = read_evidence(Path(source))
        if evidence is None:
            evidence = found
        else:
            evidence.extend(found)
    if evidence is None or not (evidence.facts or evidence.cautions
                                or evidence.absent):
        return None

    absent = sorted({a.name for a in evidence.absent})
    solver_absent = [n for n in absent if n.lower() in SOLVER_ARTIFACTS]
    return {
        "release": _first(evidence, "project.ansys_release"),
        "lastSaved": _first(evidence, "project.last_saved_utc"),
        "nFacts": len(evidence.facts),
        "severityCounts": evidence.severity_counts,
        "cautions": [
            {"severity": c.severity, "summary": c.summary}
            for c in _distinct(evidence.cautions)[:MAX_CAUTIONS]
        ],
        "nDistinctCautions": len(_distinct(evidence.cautions)),
        "absent": (solver_absent + [n for n in absent if n not in solver_absent])[:MAX_ABSENT],
        "nAbsent": len(absent),
        "redaction": evidence.redaction_summary,
    }


def render(summary: dict | None) -> str:
    """Markdown for the results page. Empty string when there is nothing to say."""
    if not summary:
        return ""

    lines = ["**Solver artifacts.**"]
    if summary.get("release"):
        saved = summary.get("lastSaved")
        stamp = f", last saved {saved}" if saved else ""
        lines.append(
            f"Written by {summary['release']}{stamp}. Recorded here because the "
            f"release that wrote an archive is not always the one that produced "
            f"the published results. A later re-save is the ordinary reason.")
    lines.append(f"{summary['nFacts']} value(s) read directly from the artifacts.")

    counts = summary.get("severityCounts") or {}
    if counts:
        detail = ", ".join(f"{n} {sev}" for sev, n in sorted(counts.items()))
        lines.append(
            f"\n**Cautions the solver reported** ({detail}). These are the "
            f"solver's own messages, carried through as evidence, not findings "
            f"of this tool, and not weakeners:")
        lines += [f"- {c['severity'].upper()}: {c['summary']}"
                  for c in summary.get("cautions", [])]
        remaining = summary.get("nDistinctCautions", 0) - len(summary.get("cautions", []))
        if remaining > 0:
            lines.append(f"- … and {remaining} further distinct message(s).")

    if summary.get("absent"):
        lines.append(
            f"\n**Stated absent by the package itself** "
            f"({summary['nAbsent']} file(s)). The archive records what it was "
            f"written without:")
        lines.append(", ".join(f"`{name}`" for name in summary["absent"]))

    if summary.get("redaction"):
        lines.append(f"\n*{summary['redaction'].capitalize()} before display.*")
    return "\n".join(lines)


def _first(evidence, key: str) -> str:
    found = evidence.by_key(key)
    return str(found[0].value) if found else ""


def _distinct(cautions: list) -> list:
    seen: set[str] = set()
    out = []
    for caution in cautions:
        if caution.summary in seen:
            continue
        seen.add(caution.summary)
        out.append(caution)
    return out
