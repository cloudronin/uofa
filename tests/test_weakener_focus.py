"""Weakener -> credibility-factor focus: IRI resolution + the pack-declared
semantic map. The map is NOT hardcoded in Python — it is loaded from each pack's
detection-capability `factorFocus` payload (see AGENTS.md §3), so these tests
also guard that the manifests stay the source of truth and that no pack declares
a focus factor that isn't a real factor for that pack.
"""

from __future__ import annotations

from uofa_cli import paths
from uofa_cli.weakener_focus import (
    enrich_firings,
    expected_factors,
    factor_focus,
    resolve_factor_names,
)


def _by_id(enriched):
    return {f["patternId"]: f["factors"] for f in enriched}


# ── expected factor universe ──

def test_expected_factor_counts():
    assert len(expected_factors("vv40")) == 13
    assert len(expected_factors("nasa-7009b")) == 19


# ── IRI resolution (factor-scoped firings) ──

def test_resolve_factor_names_from_iri():
    slug_to_name = {"use-error": "Use error", "model-form": "Model form"}
    nodes = ["https://x/cou/factor/use-error", "https://x/cou/factor/model-form",
             "https://x/validation/foo"]  # non-factor node ignored
    assert resolve_factor_names(nodes, slug_to_name) == ["Use error", "Model form"]


# ── the semantic map is loaded from the packs, not from code ──

def test_focus_index_matches_manifests():
    # core declares the base map; nasa augments W-PROV-01.
    vv = paths.factor_focus_index(["vv40"])
    nasa = paths.factor_focus_index(["nasa-7009b"])
    assert vv["W-AR-05"] == ["Output comparison"]
    assert vv["W-PROV-01"] == ["Output comparison"]
    assert vv["W-ON-02"] == ["Relevance of the validation activities to the COU"]
    # NASA unions in its provenance factor without losing the core mapping.
    assert nasa["W-PROV-01"] == ["Output comparison", "Data pedigree"]


def test_declared_focus_names_are_real_factors_for_their_pack():
    # A pack must not declare a focus factor name that isn't one of its factors —
    # that would be a silent authoring typo the loader can only drop.
    for pack in ("core", "vv40", "nasa-7009b"):
        manifest = paths.pack_manifest(pack)
        focus = paths.detection_config(manifest).get("factorFocus") or {}
        # core's names must be valid for the base (vv40) factor set it ships for.
        universe = set(expected_factors("nasa-7009b" if pack == "nasa-7009b" else "vv40"))
        for pid, names in focus.items():
            for fac in names:
                assert fac in universe, f"{pack}:{pid} declares unknown factor {fac!r}"


# ── enrich_firings: IRI ∪ pack focus, filtered to the pack ──

def _firings():
    return [
        {"patternId": "W-PROV-01", "severity": "Critical",
         "affected_nodes": ["https://x/comparator/a"]},          # non-factor node
        {"patternId": "W-EP-04", "severity": "High",
         "affected_nodes": ["https://x/cou2/factor/use-error"]},  # factor IRI
        {"patternId": "W-AL-02", "severity": "Medium",
         "affected_nodes": ["https://x/uofa"]},                   # unmapped, non-factor
    ]


def test_enrich_vv40_attaches_semantic_focus():
    out = _by_id(enrich_firings(_firings(), "vv40"))
    assert out["W-PROV-01"] == ["Output comparison"]   # from pack map
    assert out["W-EP-04"] == ["Use error"]             # from IRI
    assert out["W-AL-02"] == []                         # unmapped


def test_enrich_nasa_adds_data_pedigree_and_drops_foreign_names():
    out = _by_id(enrich_firings(_firings(), "nasa-7009b"))
    # Data pedigree is a NASA factor, so it survives the expected-factor filter.
    assert out["W-PROV-01"] == ["Output comparison", "Data pedigree"]


def test_focus_factor_filters_names_not_in_pack():
    # "Data pedigree" is declared for nasa but is NOT a vv40 factor: the filter
    # must drop it so a vv40 report never attributes a foreign factor.
    firing = {"patternId": "W-PROV-01", "affected_nodes": []}
    focus_map = {"W-PROV-01": ["Output comparison", "Data pedigree"]}
    expected = set(expected_factors("vv40"))
    got = factor_focus(firing, "vv40", focus_map, {}, expected)
    assert got == ["Output comparison"]
