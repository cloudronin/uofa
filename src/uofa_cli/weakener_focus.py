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
from uofa_cli.excel_constants import (
    AI_800_3_FACTOR_NAMES, MRM_NIST_FACTOR_NAMES, NASA_ALL_FACTOR_NAMES,
    VV40_FACTOR_NAMES,
)
from uofa_cli.excel_mapper import slugify


def _is_model_credibility(pack: str) -> bool:
    p = (pack or "").lower()
    return "mrm-nist" in p or "mrm_nist" in p or "model-credibility" in p


def expected_factors(pack: str) -> list[str]:
    """Canonical credibility-factor names for a pack (the *completeness* universe).

    This is the denominator. `report_state` counts evidenced factors against it
    and renders one grid entry per name, so a name added here is a name every
    assessed model is measured against.

    For the model-credibility pack that means **Group A only**. Group B
    (evaluation sufficiency) is deliberately absent: those factors are assessed
    by weakeners on a reported benchmark result, not by presence-counting a
    model card. Including them would score a card-only model 11/23 instead of
    11/17 — penalizing it for evaluation factors it never claimed, which is the
    firewall violation the pack spec forbids in the completeness direction.
    Use `attributable_factors` when you need the names a weakener may implicate.
    """
    if _is_model_credibility(pack):
        return MRM_NIST_FACTOR_NAMES
    p = (pack or "").lower()
    if "nasa" in p:
        return NASA_ALL_FACTOR_NAMES
    return VV40_FACTOR_NAMES


def attributable_factors(pack: str) -> list[str]:
    """Every factor name a weakener firing may be attributed to.

    Superset of `expected_factors`: it adds the factor names that exist to be
    *implicated by a finding* rather than counted for completeness. Only the
    factorFocus filter should use this — a Group-B focus entry filtered against
    the completeness universe alone would be silently dropped, and the eval
    weakeners would report into a void.
    """
    if _is_model_credibility(pack):
        return MRM_NIST_FACTOR_NAMES + AI_800_3_FACTOR_NAMES
    return expected_factors(pack)


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
    # attributable_factors, not expected_factors: a firing may implicate a factor
    # that is not part of the completeness denominator. For model-credibility that
    # is the whole Group-B set — filtering against the Group-A universe alone
    # would drop every W-EV-* attribution on the floor.
    expected = set(attributable_factors(pack))
    slug_to_name = {slugify(n): n for n in expected}
    focus_map = paths.factor_focus_index([pack], root=root)
    return [
        {**f, "factors": factor_focus(f, pack, focus_map, slug_to_name, expected)}
        for f in firings
    ]
