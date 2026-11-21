"""The `--calcverif` switch and the vv40 `calcverif` manifest block.

Two contracts. The resolver follows the same five-step order as
`uofa_cli.oos.config` (spec v0.3, section 6). The manifest block is
default-off, additive, and consistent with the rule file it names: every id
it declares has a rule, every rule's id is declared, every id is accepted by
the live C2 patternId regex (read from the SHACL, not copied), and none
collides with a pattern any pack already declares.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.calcverif import config as cv
from uofa_cli.solver import mesh_study
from uofa_cli.weakener_focus import attributable_factors

RULES_REL = "rules/calcverif/calcverif_v0.1.rules"


def _block(pack="vv40"):
    return paths.detection_config(paths.pack_manifest(pack))["calcverif"]


# ── Resolver: the five cases ────────────────────────────────────────────────


def test_case1_both_flags_is_an_error():
    with pytest.raises(cv.CalcVerifConfigError, match="mutually exclusive"):
        cv.resolve("vv40", enable_flag=True, disable_flag=True)


def test_case2_flag_on_loads_the_declared_rule_file():
    cfg = cv.resolve("vv40", enable_flag=True)
    assert cfg.enabled is True and cfg.source == cv.SOURCE_CLI_FORCE_ON
    assert cfg.rule_files == [(paths.pack_dir("vv40") / RULES_REL).resolve()]


def test_case2_flag_on_against_a_pack_without_the_block_is_an_error():
    with pytest.raises(cv.CalcVerifConfigError, match="does not declare"):
        cv.resolve("nasa-7009b", enable_flag=True)


def test_case3_flag_off():
    cfg = cv.resolve("vv40", disable_flag=True)
    assert (cfg.enabled, cfg.rule_files, cfg.source) == (False, [], cv.SOURCE_CLI_FORCE_OFF)


def test_case4_pack_block_decides_and_vv40_says_off():
    cfg = cv.resolve("vv40")
    assert (cfg.enabled, cfg.rule_files, cfg.source) == (False, [], cv.SOURCE_PACK_CONFIG)


def test_case5_pack_without_block_is_off():
    cfg = cv.resolve("nasa-7009b")
    assert (cfg.enabled, cfg.rule_files, cfg.source) == (False, [], cv.SOURCE_PACK_DEFAULT_OMITTED)


def _fake_pack(tmp_path, block):
    """A one-pack repo root whose vv40-shaped manifest carries `block`."""
    manifest = paths.pack_manifest("vv40")
    for cap in manifest["capabilities"]:
        if cap.get("leg") == "detection":
            cap["payload"]["calcverif"] = block
    pack = tmp_path / "packs" / "fake"
    (pack / "rules" / "calcverif").mkdir(parents=True)
    (pack / "pack.json").write_text(json.dumps(manifest))
    shutil.copy(paths.pack_dir("vv40") / RULES_REL, pack / RULES_REL)
    return tmp_path


def test_case4_honours_enabled_true_from_the_pack(tmp_path):
    root = _fake_pack(tmp_path, {"enabled": True, "rule_files": [RULES_REL]})
    cfg = cv.resolve("fake", root=root)
    assert cfg.enabled is True and cfg.source == cv.SOURCE_PACK_CONFIG
    assert cfg.rule_files == [(root / "packs" / "fake" / RULES_REL).resolve()]


def test_enabled_without_rule_files_is_an_error(tmp_path):
    root = _fake_pack(tmp_path, {"enabled": True})
    with pytest.raises(cv.CalcVerifConfigError, match="no `calcverif.rule_files`"):
        cv.resolve("fake", root=root)


def test_declared_rule_file_must_exist(tmp_path):
    root = _fake_pack(tmp_path, {"enabled": False, "rule_files": ["rules/calcverif/missing.rules"]})
    with pytest.raises(cv.CalcVerifConfigError, match="does not exist"):
        cv.resolve("fake", enable_flag=True, root=root)


# ── The shipped vv40 block ──────────────────────────────────────────────────


def test_vv40_block_ships_off():
    assert _block()["enabled"] is False


def test_vv40_default_pattern_count_is_still_zero():
    assert paths.detection_config(paths.pack_manifest("vv40"))["patternIds"] == []


def test_calcverif_ids_are_not_in_any_pack_level_index():
    """Declared only inside the block, so no default loader picks them up."""
    index = paths.patternid_pack_index()
    assert not [pid for pid in _block()["patternIds"] if pid in index]


def _c2_pattern() -> str:
    """The live patternId regex from the C2 WeakenerAnnotationShape."""
    rdflib = pytest.importorskip("rdflib")
    sh = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    uofa = rdflib.Namespace("https://uofa.net/vocab#")
    g = rdflib.Graph().parse(str(paths.shacl_schema()), format="turtle")
    for prop in g.objects(uofa.WeakenerAnnotationShape, sh.property):
        if g.value(prop, sh.path) == uofa.patternId:
            pattern = g.value(prop, sh.pattern)
            if pattern is not None:
                return str(pattern)
    raise AssertionError("WeakenerAnnotationShape declares no patternId sh:pattern")


def test_block_ids_pass_the_live_c2_regex():
    rx = re.compile(_c2_pattern())
    ids = _block()["patternIds"]
    assert ids == ["W-CV-01", "W-CV-02", "W-CV-03", "W-CV-04"]
    assert all(rx.fullmatch(pid) for pid in ids)


def test_block_ids_collide_with_no_declared_pattern():
    declared = set()
    for name in paths.list_packs(paths.find_repo_root()):
        manifest = paths.pack_manifest(name)
        for cap in manifest.get("capabilities", []):
            declared |= set((cap.get("payload") or {}).get("patternIds") or [])
    assert not declared & set(_block()["patternIds"])


def test_block_ids_and_rule_file_agree():
    block = _block()
    assert block["rule_files"] == [RULES_REL]
    text = (paths.pack_dir("vv40") / RULES_REL).read_text()
    in_rules = set(re.findall(r"uofa:patternId '([^']+)'", text))
    assert in_rules == set(block["patternIds"])
    headers = set(re.findall(r"^# (W-CV-\d{2}): ", text, flags=re.M))
    assert headers == set(block["patternIds"])


def test_factor_focus_names_are_vv40_factors():
    focus = _block()["factorFocus"]
    assert set(focus) == set(_block()["patternIds"])
    names = set(attributable_factors("vv40"))
    assert all(set(v) <= names for v in focus.values())


def test_rule_bodies_name_no_factor():
    """Joins go through the shared factor name; no factor is hardcoded."""
    text = (paths.pack_dir("vv40") / RULES_REL).read_text()
    bodies = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
    for name in attributable_factors("vv40"):
        assert f"'{name}'" not in bodies


def test_gci_identity_entry_is_what_the_wrapper_reads():
    identity = paths.detection_config(paths.pack_manifest("vv40"))["quantityIdentity"]
    entry = identity[mesh_study.GCI_RELATIVE]
    assert entry == {"canonicalUnit": "fraction", "tolerance": 0.25,
                     "units": {"fraction": 1.0, "%": 0.01}}
