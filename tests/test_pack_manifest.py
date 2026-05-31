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
