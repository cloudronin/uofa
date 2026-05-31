"""P5 — the C2↔C3 patternId contract is internally consistent and stays that way.

The C2 quality gate (`uofa:WeakenerAnnotationShape` `sh:pattern`) must accept
every patternId the C3 detection packs actually emit. The investigation found it
didn't: the old regex enumerated `(EP|AL|ON|AR|SI|NASA|CON|PROV)` with exactly two
digits, so it rejected the surrogate pack's `W-SURR-0x` and iso42001's
word-suffixed `W-AIMS-*` ids — a latent C2↔C3 drift.

These tests are **data-driven**: the accepted vocabulary is read from the loaded
pack manifests (not hardcoded here), and checked against the regex extracted from
the SHACL itself (not a copy). So if any pack later declares a patternId the C2
shape would reject — or someone narrows the shape — this fails, and the drift
cannot silently reopen.
"""

from __future__ import annotations

import json
import re

import pytest

from uofa_cli import paths

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, Namespace  # noqa: E402

SH = Namespace("http://www.w3.org/ns/shacl#")
UOFA = Namespace("https://uofa.net/vocab#")


def _c2_pattern() -> str:
    """The live patternId regex from the C2 WeakenerAnnotationShape (authoritative)."""
    g = Graph().parse(str(paths.shacl_schema()), format="turtle")
    for prop in g.objects(UOFA.WeakenerAnnotationShape, SH.property):
        if g.value(prop, SH.path) == UOFA.patternId:
            pattern = g.value(prop, SH.pattern)
            if pattern is not None:
                return str(pattern)
    raise AssertionError("WeakenerAnnotationShape declares no patternId sh:pattern")


def _declared_pattern_ids() -> dict[str, str]:
    """{patternId: owning pack} across every installed pack's detection capability."""
    root = paths.find_repo_root()
    owners: dict[str, str] = {}
    for name in paths.list_packs(root):
        manifest = paths.pack_manifest(name, root=root)
        for cap in manifest.get("capabilities", []):
            for pid in (cap.get("payload") or {}).get("patternIds") or []:
                owners.setdefault(pid, name)
    return owners


def test_c2_accepts_every_declared_patternid():
    rx = re.compile(_c2_pattern())
    owners = _declared_pattern_ids()
    assert owners, "no patternIds discovered — manifests not loading?"
    rejected = {pid: pack for pid, pack in owners.items() if not rx.match(pid)}
    assert not rejected, (
        f"C2 WeakenerAnnotationShape rejects patternIds the packs declare "
        f"(C2↔C3 drift): {rejected}"
    )


@pytest.mark.parametrize("pid", ["W-SURR-03", "W-AIMS-AUDIT-STALE", "W-AIMS-MODEL-EVAL-STALE"])
def test_c2_accepts_previously_excluded_families(pid):
    # The exact ids the old enumerated regex rejected — pinned so a regression
    # to an enumerated family list fails loudly.
    assert re.compile(_c2_pattern()).match(pid)


@pytest.mark.parametrize("bad", ["INVALID", "W-ep-01", "FOO-01", "W-EP-1", "weakener 1", "COMPOUND-1"])
def test_c2_still_rejects_malformed_patternids(bad):
    # Broadened, not removed: the shape is still a real gate (not `.*`).
    assert not re.compile(_c2_pattern()).match(bad)


def test_patternid_pack_index_attributes_to_owning_pack():
    index = paths.patternid_pack_index()
    # Each pack's distinctive ids resolve to that pack.
    assert index.get("W-EP-04") == "core"
    assert index.get("W-AIMS-AUDIT-STALE") == "iso42001"
    assert index.get("W-SURR-03") == "surrogate"
    assert index.get("W-NASA-01") == "nasa-7009b"
    # A base id reused by a pack stays owned by core (first declarer wins).
    assert index.get("W-PROV-01") == "core"
    # Every declared id is in the index.
    assert set(_declared_pattern_ids()) <= set(index)


def test_attribute_firings_stamps_owning_pack():
    from uofa_cli.commands.rules import attribute_firings
    firings = [
        {"patternId": "W-AIMS-AUDIT-STALE", "severity": "High", "hits": 1},
        {"patternId": "W-EP-04", "severity": "High", "hits": 6},
        {"patternId": "W-SURR-03", "severity": "High", "hits": 1},
        {"patternId": "W-NOPE-99", "severity": "Low", "hits": 1},  # unrecognized
    ]
    attribute_firings(firings)
    assert [f["pack"] for f in firings] == ["iso42001", "core", "surrogate", None]


def test_derived_json_schema_pattern_in_sync_with_shacl():
    # spec/schemas/uofa.schema.json is generated from the SHACL (`uofa schema`).
    # If the SHACL pattern changed but the schema wasn't regenerated, catch it.
    schema = json.loads(
        (paths.find_repo_root() / "spec" / "schemas" / "uofa.schema.json").read_text(encoding="utf-8")
    )
    derived = schema["$defs"]["WeakenerAnnotationShape"]["properties"]["patternId"]["pattern"]
    assert derived == _c2_pattern(), (
        "uofa.schema.json patternId pattern is stale vs the SHACL — "
        "regenerate with `uofa schema`"
    )
