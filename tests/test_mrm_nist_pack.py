"""MRM-NIST pack: load gate, factorFocus typo guard, curated-card partition, and
the R2 firing kill gate.

The R2 gate (mrm-nist-demo-build-spec.md §4/§9): at least 6 of the 23 core patterns
must fire on real card-derived bundles, with visible cross-card contrast — else the
demo is too thin and falls back to the V&V40 render. Encoded here so the kill
criterion is a standing regression guard, derived from the curated source (not a
snapshot), so a change to the curation that drops the gate fails loudly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.excel_mapper import map_to_jsonld
from uofa_cli.weakener_focus import expected_factors

_ROOT = paths.find_repo_root()
sys.path.insert(0, str(_ROOT / "packs" / "mrm-nist" / "examples"))
from curated_cards import CARDS, build_import_dict  # noqa: E402

_HAS_JAR = paths.jar_path().exists()
_needs_engine = pytest.mark.skipif(not _HAS_JAR, reason="weakener engine JAR not built")


def test_pack_loads_and_has_17_factors():
    paths.validate_active_packs(active=["mrm-nist"])  # manifest schema + load gate
    assert len(expected_factors("mrm-nist")) == 17


def test_factorfocus_names_are_real_mrm_nist_factors():
    # A declared focus factor that isn't a real mrm-nist factor is a silent authoring
    # typo the loader can only drop (parallels tests/test_weakener_focus for the
    # core/vv40/nasa packs, which don't cover mrm-nist).
    focus = paths.detection_config(paths.pack_manifest("mrm-nist")).get("factorFocus") or {}
    assert focus, "mrm-nist should declare a factorFocus map"
    universe = set(expected_factors("mrm-nist"))
    for pid, names in focus.items():
        for fac in names:
            assert fac in universe, f"mrm-nist:{pid} declares unknown factor {fac!r}"


def test_each_card_partitions_all_17_factors():
    universe = sorted(expected_factors("mrm-nist"))
    for card in CARDS:
        seen = list(card.assessed) + list(card.not_assessed) + list(card.scoped_out)
        assert sorted(seen) == universe, f"{card.key}: factor partition gaps/extras"
        assert len(seen) == len(set(seen)) == 17, f"{card.key}: duplicate factor"


def _bundle(card, tmp_path: Path) -> Path:
    doc = map_to_jsonld(build_import_dict(card), packs=["mrm-nist"],
                        source_path=Path(card.model_id))
    from space import pipeline
    pipeline._assign_factor_ids(doc)
    p = tmp_path / f"{card.key}.jsonld"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


@_needs_engine
def test_r2_firing_gate(tmp_path):
    from space import pipeline
    union: set[str] = set()
    per_card: dict[str, frozenset] = {}
    for card in CARDS:
        p = _bundle(card, tmp_path)
        pats = frozenset(f["patternId"] for f in pipeline._run_weakeners(p, "mrm-nist"))
        per_card[card.key] = pats
        union |= pats
    assert len(union) >= 6, f"R2 kill gate: only {len(union)} distinct patterns: {sorted(union)}"
    assert len(set(per_card.values())) > 1, "cards must differ — no contrast to show"


@_needs_engine
def test_card_bundle_has_no_factortype_shacl_violation(tmp_path):
    # The central P0 gotcha: mrm-nist factors must carry factorStandard so the vv40
    # name shape (which has an `!BOUND(?fs)` backward-compat clause) does not flag
    # them. Only the honest structural gap (no bound requirement) may remain.
    from space import pipeline
    p = _bundle(CARDS[0], tmp_path)  # OLMo — the well-documented card
    _conforms, violations = pipeline._run_check(p, "mrm-nist")
    bad = {str(v.get("path")) for v in violations}
    assert not any("factorType" in b for b in bad), f"factorType wrongly flagged: {bad}"
    assert bad <= {"bindsRequirement"}, f"violations beyond the honest card gap: {bad}"
