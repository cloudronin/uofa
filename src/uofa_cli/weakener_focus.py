"""Resolve which credibility factor(s) a weakener firing implicates.

A firing's `affectedNode` is sometimes a `.../factor/<slug>` IRI (W-EP-04,
W-NASA-*) — those resolve to a factor name directly. But most High/Critical
weakeners fire on a validation-result or COU node (W-AR-05, W-PROV-01, W-ON-02),
so IRI resolution alone yields no factor and the concern can demote nothing —
the credibility-factor axis and the concern axis never meet.

This module closes that gap by attaching each firing's *semantic* factor focus.
The pattern→factor map is **not** hardcoded here: it is declared per-pack in the
detection-capability `factorFocus` payload and loaded via
`paths.factor_focus_index`, so it tracks the packs (a pack adding/renaming a
pattern updates its own manifest). Core patterns are declared in `packs/core`;
a pack augments them (NASA adds `Data pedigree` to `W-PROV-01`). Every attached
name is filtered to the bundle pack's expected factors, so a foreign-pack name
is never mis-attributed.

Pure read-side interpretation of engine output: the rule engine, shapes, and
`.rules` files are untouched.
"""

from __future__ import annotations

from uofa_cli import paths
from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES
from uofa_cli.excel_mapper import slugify


def expected_factors(pack: str) -> list[str]:
    """Canonical credibility-factor names for a pack (the factor universe)."""
    return NASA_ALL_FACTOR_NAMES if "nasa" in (pack or "").lower() else VV40_FACTOR_NAMES


def resolve_factor_names(affected_nodes, slug_to_name: dict[str, str]) -> list[str]:
    """Map `.../factor/<slug>` affectedNode IRIs back to canonical factor names."""
    names: list[str] = []
    for node in affected_nodes or []:
        if "/factor/" in str(node):
            slug = str(node).rsplit("/factor/", 1)[1]
            name = slug_to_name.get(slug)
            if name and name not in names:
                names.append(name)
    return names


def factor_focus(
    firing: dict,
    pack: str,
    focus_map: dict[str, list[str]],
    slug_to_name: dict[str, str],
    expected: set[str],
) -> list[str]:
    """Factors a single firing implicates: IRI-resolved ∪ the pattern's declared
    semantic focus, filtered to factors expected for `pack`, order-preserving."""
    names = resolve_factor_names(firing.get("affected_nodes", []), slug_to_name)
    pattern = firing.get("patternId") or firing.get("pattern_id") or ""
    for fac in focus_map.get(pattern, ()):  # declared in pack manifests, not here
        if fac in expected and fac not in names:
            names.append(fac)
    return names


def enrich_firings(firings: list[dict], pack: str, root=None) -> list[dict]:
    """Return `firings` with a `factors` key on each, computed from the
    pack-declared focus map plus affectedNode IRI resolution. Non-mutating:
    callers that re-use raw firings (e.g. the `--explain` pipeline) are
    unaffected. `pack` is the bundle's pack; the focus map merges core + pack."""
    expected = set(expected_factors(pack))
    slug_to_name = {slugify(n): n for n in expected}
    focus_map = paths.factor_focus_index([pack], root=root)
    return [
        {**f, "factors": factor_focus(f, pack, focus_map, slug_to_name, expected)}
        for f in firings
    ]
