"""Free-tier findings: completeness + weakeners, computed honestly.

Completeness is owned by us (derived from the confirmed factor statuses, not
re-discovered from SHACL). Weakeners come from the rule engine; factor-scoped
firings are attributed to factor names via the stable `.../factor/<slug>` IRIs
the pipeline injects. SHACL violations are surfaced as global structural
findings (they carry path/severity, not a factor focus). There is deliberately
NO Accepted/Not-Accepted headline - that verdict is a human act and is deferred.
"""

from __future__ import annotations

from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES
from uofa_cli.excel_mapper import slugify

_EXCLUDED_STATUSES = ("scoped-out", "not-applicable")

# Semantic weakener -> credibility-factor focus (closes the engine/extraction
# axis gap). Most High/Critical weakeners fire on a validation-result or COU
# node, never on a `.../factor/<slug>` IRI, so IRI resolution alone leaves their
# `factors` empty: the concern cannot demote the credibility factor it actually
# implicates, and a factor extraction over-marked "assessed" stays "Evidenced"
# even while a Critical concern disputes its basis (the Build B contradiction).
# This map records, per pattern, the factor(s) the concern bears on, so the
# reviewer view demotes the right factor (see reviewer_state.build_reviewer_state)
# and the concern line reads "Relates to: <factor>".
#
# Deliberately conservative: only patterns with a single, defensible factor
# implication are mapped. Broad/meta concerns (COMPOUND-01 escalation) and
# uncertainty/sensitivity concerns (W-AL-*, W-CON-04) that V&V40 does not model
# as a standalone credibility factor stay unmapped and surface through the
# open-concern framing. Values are canonical VV40 factor names; any name not
# expected for the active pack is dropped, so a pack without that factor (e.g.
# NASA) is unaffected rather than mis-attributed.
_PATTERN_FACTOR_FOCUS: dict[str, list[str]] = {
    # Comparator data is absent (no comparedAgainst link) or its provenance chain
    # terminates without a documented source -> the output-vs-reference
    # comparison the factor certifies is unsupported.
    "W-AR-05": ["Output comparison"],
    "W-PROV-01": ["Output comparison"],
    # COU declared with no applicability constraint / operating envelope -> its
    # boundary of validity is undocumented, so the validation activities cannot
    # be shown relevant to the context of use.
    "W-ON-02": ["Relevance of the validation activities to the COU"],
}


def expected_factors(pack: str) -> list[str]:
    return NASA_ALL_FACTOR_NAMES if "nasa" in pack.lower() else VV40_FACTOR_NAMES


def _resolve_factor_names(affected_nodes: list[str], slug_to_name: dict[str, str]) -> list[str]:
    """Map `.../factor/<slug>` IRIs back to canonical factor names."""
    names = []
    for node in affected_nodes or []:
        if "/factor/" in str(node):
            slug = str(node).rsplit("/factor/", 1)[1]
            name = slug_to_name.get(slug)
            if name and name not in names:
                names.append(name)
    return names


def _factor_focus(firing: dict, slug_to_name: dict[str, str], expected: set[str]) -> list[str]:
    """The credibility factors a firing implicates: those its affectedNode IRIs
    resolve to, plus the pattern's semantic focus (`_PATTERN_FACTOR_FOCUS`) for
    validation/COU-scoped concerns that target no factor IRI. Semantic names are
    kept only when expected for the pack, so a foreign-pack name is never
    attributed."""
    names = _resolve_factor_names(firing.get("affected_nodes", []), slug_to_name)
    pattern = firing.get("patternId") or firing.get("pattern_id") or ""
    for name in _PATTERN_FACTOR_FOCUS.get(pattern, ()):
        if name in expected and name not in names:
            names.append(name)
    return names


def _headline(n_assessed: int, n_expected: int, n_missing: int, firings: list[dict], sev_counts: dict[str, int]) -> str:
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


def compute(pack: str, factor_statuses: dict[str, str], shacl: dict, firings: list[dict]) -> dict:
    """Assemble the free-tier summary payload.

    Args:
        factor_statuses: factor_type -> confirmed status (what we own).
        shacl: {"conforms": bool, "violations": [ {path, message, severity}, ... ]}.
        firings: rich firing dicts from parse_firings_jsonld.
    """
    expected = expected_factors(pack)
    assessed = [n for n in expected if factor_statuses.get(n) == "assessed"]
    missing = [n for n in expected if factor_statuses.get(n) == "not-assessed"]
    excluded = [n for n in expected if factor_statuses.get(n) in _EXCLUDED_STATUSES]
    denom = len(expected) - len(excluded)

    slug_to_name = {slugify(n): n for n in expected}
    expected_set = set(expected)
    sev_counts: dict[str, int] = {}
    enriched = []
    for w in firings:
        sev = w.get("severity", "Medium")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        enriched.append({**w, "factors": _factor_focus(w, slug_to_name, expected_set)})

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
