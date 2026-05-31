"""P2a — pack-manifest schema + load-time validation (pack-shaped spec §7).

The §7 compatibility contract replaces the old bare ``json.loads`` + dir-exists
check with real schema validation at the load gate. These tests pin: every
installed pack validates (the legacy flat form is still accepted during the
migration), a malformed manifest fails loudly, and the schema forward-accepts
the new ``capabilities[]`` envelope.
"""

from __future__ import annotations

import pytest

from uofa_cli import paths


def test_all_installed_packs_validate():
    root = paths.find_repo_root()
    names = paths.list_packs(root)
    assert "core" in names and "surrogate" in names  # sanity: packs discovered
    for name in names:
        paths.validate_pack_manifest(paths.pack_manifest(name, root=root), name, root=root)


@pytest.mark.parametrize("bad", [
    {"version": "0.1.0"},                                   # missing required name
    {"name": "x", "version": "not-semver"},                 # version pattern
    {"name": "BadName", "version": "0.1.0"},                # name pattern (uppercase)
    {"name": "x", "version": "0.1.0", "unknownField": 1},   # additionalProperties:false
])
def test_malformed_manifest_raises(bad):
    with pytest.raises(ValueError):
        paths.validate_pack_manifest(bad, "test", root=paths.find_repo_root())


def test_schema_forward_accepts_capabilities_block():
    root = paths.find_repo_root()
    new_form = {
        "name": "demo", "version": "0.1.0", "coreCompatibility": ">=0.5.0",
        "dependencies": [{"pack": "core", "range": ">=0.5.0"}],
        "capabilities": [{
            "leg": "measurement", "capabilityId": "measurement:envelope-distance",
            "targetInterface": "MeasurementMethod", "interfaceVersion": "1.0",
            "firewallPlacement": "measurement-region",
            "payload": {"impl": "pkg.mod:Cls", "outputKeys": ["envelopeCoverage"]},
        }],
    }
    paths.validate_pack_manifest(new_form, "demo", root=root)  # must not raise


@pytest.mark.parametrize("bad_cap", [
    {"leg": "bogus", "capabilityId": "detection:x", "targetInterface": "I",
     "interfaceVersion": "1.0", "firewallPlacement": "measurement-region"},      # bad leg
    {"leg": "measurement", "capabilityId": "measurement:x", "targetInterface": "I",
     "interfaceVersion": "1.0", "firewallPlacement": "bogus-region"},            # bad placement
    {"leg": "measurement", "capabilityId": "BADID", "targetInterface": "I",
     "interfaceVersion": "1.0", "firewallPlacement": "measurement-region"},      # bad capabilityId
])
def test_malformed_capability_raises(bad_cap):
    root = paths.find_repo_root()
    manifest = {"name": "demo", "version": "0.1.0", "capabilities": [bad_cap]}
    with pytest.raises(ValueError):
        paths.validate_pack_manifest(manifest, "demo", root=root)


def test_validate_active_packs_enforces_at_load_gate():
    prev = paths.get_active_pack()
    paths.set_active_pack(["surrogate"])
    try:
        paths.validate_active_packs()  # core + surrogate manifests both conform → no raise
    finally:
        paths.set_active_pack(prev)


# ── P2c: cross-pack compatibility enforcement ───────────────────────────────


def test_version_helpers():
    assert paths._version_tuple("0.5.0") == (0, 5, 0)
    assert paths._satisfies("0.5.0", ">=0.5.0")
    assert paths._satisfies("0.6.1", ">=0.5.0")
    assert not paths._satisfies("0.4.9", ">=0.5.0")
    assert paths._satisfies("1.0", "==1.0")


def _detcap(pack, pids, *, iface_ver="1.0", iface="detection"):
    return (pack, {"name": pack, "version": "0.1.0", "capabilities": [
        {"leg": "detection", "capabilityId": f"detection:{pack}",
         "targetInterface": iface, "interfaceVersion": iface_ver,
         "firewallPlacement": "measurement-region",
         "payload": {"patternIds": pids}}]})


def test_enforce_allows_core_pattern_reuse_by_a_pack():
    # core declares W-PROV-01; an iso-like pack reuses it — NOT a collision
    # (core's patternIds are the reusable base vocabulary).
    manifests = [
        ("core", {"name": "core", "version": "0.5.0", "capabilities": [
            {"leg": "detection", "capabilityId": "detection:core", "targetInterface": "detection",
             "interfaceVersion": "1.0", "firewallPlacement": "measurement-region",
             "payload": {"patternIds": ["W-PROV-01", "W-AR-02"]}}]}),
        _detcap("isolike", ["W-PROV-01", "W-AIMS-X"]),
    ]
    paths._enforce_pack_compatibility(manifests, "0.5.0", ["isolike"])  # must not raise


def test_enforce_flags_collision_between_two_noncore_packs():
    manifests = [_detcap("p1", ["W-DUP-01"]), _detcap("p2", ["W-DUP-01"])]
    with pytest.raises(ValueError, match="collision"):
        paths._enforce_pack_compatibility(manifests, "0.5.0", ["p1", "p2"])


def test_enforce_core_compatibility_range():
    m = [("x", {"name": "x", "version": "0.1.0", "coreCompatibility": ">=99.0.0", "capabilities": []})]
    with pytest.raises(ValueError, match="requires core"):
        paths._enforce_pack_compatibility(m, "0.5.0", [])


def test_enforce_interface_version_major_mismatch():
    with pytest.raises(ValueError, match="major mismatch"):
        paths._enforce_pack_compatibility([_detcap("x", ["W-X-01"], iface_ver="2.0")], "0.5.0", ["x"])


def test_enforce_unknown_interface():
    # `detection` and `measurement` are known core interfaces (P2c, P3); a
    # capability targeting an interface the core does NOT provide fails loudly.
    with pytest.raises(ValueError, match="unknown"):
        paths._enforce_pack_compatibility([_detcap("x", [], iface="no-such-interface")], "0.5.0", ["x"])


def test_enforce_missing_dependency():
    m = [("x", {"name": "x", "version": "0.1.0",
                "dependencies": [{"pack": "ghost", "range": ">=1.0.0"}], "capabilities": []})]
    with pytest.raises(ValueError, match="not installed"):
        paths._enforce_pack_compatibility(m, "0.5.0", ["x"])


def test_validate_active_packs_real_sets_pass_enforcement():
    prev = paths.get_active_pack()
    try:
        for pack in ("surrogate", "iso42001", "nasa-7009b", "vv40"):
            paths.set_active_pack([pack])
            paths.validate_active_packs()  # core + pack (incl shared-id reuse) → no raise
    finally:
        paths.set_active_pack(prev)
