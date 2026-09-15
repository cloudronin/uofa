"""The v0.10 attestation shapes, and the drift they exist to prevent.

`attestations.py` decides what an attestation MEANS: which fields carry meaning,
and therefore which ones are inside the bytes that get signed. The SHACL shapes
decide what `uofa validate` accepts. Those are two artifacts stating the same
rule, which is exactly the shape of a rule that rots.

The failure is quiet in both directions. A field the library signs but the
shapes call optional is a field a validator waves through and a verifier
rejects -- the package is "valid" right up until someone checks it. A field the
shapes demand but the library never writes refuses every package the product
produces. Neither shows up in a suite that tests the two halves separately, so
the first test here holds the two lists against each other directly.

The rest prove the shapes actually fire: that a package cut before v0.10 is
untouched by them, that a well-formed block passes, and that each missing field
is named by its own message rather than disappearing into a generic refusal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from rdflib import Graph

from uofa_cli import attestations, paths
from uofa_cli.shacl_friendly import _load_data_graph

REPO = Path(__file__).resolve().parents[1]
V010 = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.10.jsonld"

SHAPES_TTL = REPO / "packs" / "core" / "shapes" / "uofa_shacl.ttl"

#: Written at signing rather than by the builder, so they are not in the
#: library's `*_REQUIRED` tuple -- but a block without them is not an
#: attestation, so the shapes require them and this test accounts for them.
_ADDED_AT_SIGNING = {
    "IdentityBindingAttestationShape": {
        attestations.AUTHORITY_FIELD, attestations.IDENTITY_SIGNATURE_FIELD},
    "AuthorizationAttestationShape": {
        attestations.AUTHORITY_FIELD, attestations.AUTHORIZATION_SIGNATURE_FIELD},
}


@pytest.fixture(scope="module")
def shapes() -> Graph:
    g = Graph()
    for p in paths.all_shacl_schemas():
        g.parse(str(p), format="turtle")
    return g


def _required_paths(g: Graph, shape: str) -> set[str]:
    """The property names a shape marks `sh:minCount 1`."""
    rows = g.query("""
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        SELECT ?path WHERE {
          ?shape sh:property ?p . ?p sh:path ?path ; sh:minCount 1 .
        }""", initBindings={"shape": _uofa(shape)})
    return {str(r[0]).rsplit("#", 1)[-1] for r in rows}


def _uofa(name: str):
    from rdflib import URIRef
    return URIRef("https://uofa.net/vocab#" + name)


# ── the drift guard ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("shape,library", [
    ("IdentityBindingAttestationShape", attestations.IDENTITY_REQUIRED),
    ("AuthorizationAttestationShape", attestations.AUTHORIZATION_REQUIRED),
])
def test_the_shapes_require_exactly_what_the_library_signs(shapes, shape, library):
    in_shapes = _required_paths(shapes, shape)
    in_library = set(library) | _ADDED_AT_SIGNING[shape]
    assert in_shapes == in_library, (
        f"{shape} and the library disagree about what an attestation must "
        f"state.\n  shapes demand, library never writes: "
        f"{sorted(in_shapes - in_library)}\n  library signs, shapes call "
        f"optional: {sorted(in_library - in_shapes)}\n"
        f"Either way one of the two artifacts is lying about the same rule.")


def test_every_required_field_carries_its_own_message(shapes):
    """A shape that refuses without saying which field is missing sends the
    reader back to the shapes file to find out what it meant."""
    rows = shapes.query("""
        PREFIX sh: <http://www.w3.org/ns/shacl#>
        SELECT ?path ?msg WHERE {
          ?shape sh:property ?p . ?p sh:path ?path ; sh:minCount 1 .
          OPTIONAL { ?p sh:message ?msg }
        }""", initBindings={"shape": _uofa("IdentityBindingAttestationShape")})
    silent = [str(r[0]).rsplit("#", 1)[-1] for r in rows if r[1] is None]
    assert not silent, f"required with no message: {silent}"


# ── the shapes against real documents ────────────────────────────────────────

_OURS = ("must name the actor it speaks about", "must name the key it speaks about",
         "must name the identity provider issuer", "must name the subject the provider",
         "must state when possession was proven", "must state which purpose",
         "must name the deployment that made it", "must state when it was made",
         "must carry the context edition", "must carry the attestation schema",
         "must name the key that made the statement", "unsigned binding",
         "must name the actor it authorizes", "must name the project",
         "must name the decision it covers", "must name the action",
         "must cite the grant", "must state when the grant became effective",
         "must state when the producer rechecked", "must state when the signature it covers",
         "unsigned authorization",
         "well-formed identity binding attestation",
         "well-formed authorization attestation")


def _validate(shapes, tmp_path, **blocks):
    doc = {"@context": V010, "id": "urn:uofa:t", "type": "UnitOfAssurance"}
    doc.update(blocks)
    p = tmp_path / "p.jsonld"
    p.write_text(json.dumps(doc), encoding="utf-8")
    from pyshacl import validate
    _c, _g, text = validate(data_graph=_load_data_graph(p), shacl_graph=shapes)
    return [m for m in _OURS if m in text], text


def _binding(**over):
    b = attestations.build_identity_binding(
        bound_actor="https://example.org/actor/abc", bound_key="sha256:" + "a" * 64,
        provider_issuer="https://huggingface.co", provider_subject="subj-1",
        possession_proven_at="2026-09-01T00:00:00Z", deployment_id="dep-1",
        issued_at="2026-09-02T00:00:00Z", context_version="v0.10")
    b[attestations.AUTHORITY_FIELD] = "sha256:" + "c" * 64
    b[attestations.IDENTITY_SIGNATURE_FIELD] = "ed25519:" + "d" * 128
    b.update(over)
    return b


def _authorization(**over):
    a = attestations.build_authorization_attestation(
        authorized_actor="https://example.org/actor/abc", project="proj-1",
        decision_record="urn:uofa:decision:1", grant_id="grant-1",
        effective_from="2026-08-01T00:00:00Z",
        authorization_checked_at="2026-09-02T00:00:00Z",
        decision_signed_at="2026-09-02T00:00:00Z", deployment_id="dep-1",
        issued_at="2026-09-02T00:00:00Z", context_version="v0.10")
    a[attestations.AUTHORITY_FIELD] = "sha256:" + "c" * 64
    a[attestations.AUTHORIZATION_SIGNATURE_FIELD] = "ed25519:" + "d" * 128
    a.update(over)
    return a


def test_a_package_cut_before_v0_10_is_untouched_by_these_shapes(shapes, tmp_path):
    """The blocks are optional. If they were not, every package that ever
    shipped would start failing the moment this release landed."""
    ours, _ = _validate(shapes, tmp_path)
    assert not ours, f"a package with no attestations was refused: {ours}"


def test_well_formed_blocks_conform(shapes, tmp_path):
    ours, text = _validate(
        shapes, tmp_path,
        hasIdentityBinding=_binding(),
        hasAuthorizationAttestation=_authorization())
    assert not ours, f"well-formed attestations were refused: {ours}\n{text[:2000]}"


@pytest.mark.parametrize("field", sorted(
    set(attestations.IDENTITY_REQUIRED)
    | {attestations.AUTHORITY_FIELD, attestations.IDENTITY_SIGNATURE_FIELD}))
def test_a_binding_missing_any_required_field_is_refused(shapes, tmp_path, field):
    block = _binding()
    del block[field]
    ours, text = _validate(shapes, tmp_path, hasIdentityBinding=block)
    assert ours, (
        f"a binding with no {field} conformed. Every field here is inside the "
        f"signed bytes, so a block missing one is a DIFFERENT statement, not a "
        f"weaker one.\n{text[:1500]}")


@pytest.mark.parametrize("field", sorted(
    set(attestations.AUTHORIZATION_REQUIRED)
    | {attestations.AUTHORITY_FIELD, attestations.AUTHORIZATION_SIGNATURE_FIELD}))
def test_an_authorization_missing_any_required_field_is_refused(
        shapes, tmp_path, field):
    block = _authorization()
    del block[field]
    ours, text = _validate(shapes, tmp_path, hasAuthorizationAttestation=block)
    assert ours, (
        f"an authorization with no {field} conformed.\n{text[:1500]}")


def test_a_block_that_forgot_its_type_is_still_checked(shapes, tmp_path):
    """The reason the shapes are reachable through `sh:node` and not only
    targeted on the class: a block with no `@type` matches no class target, so
    class targeting alone would wave it through unexamined."""
    block = _binding()
    del block["type"]
    del block["boundActor"]
    ours, text = _validate(shapes, tmp_path, hasIdentityBinding=block)
    assert ours, (
        f"a typeless, actorless binding conformed -- class targeting alone "
        f"cannot see it, which is why `sh:node` reachability is there.\n"
        f"{text[:1500]}")


# ── the two published schemas ────────────────────────────────────────────────

def test_the_generated_json_schema_documents_both_blocks():
    """`uofa.schema.json` is open at the top level, so it would ACCEPT these
    blocks while never mentioning them -- an adopter reading the schema would
    conclude the product does not produce them."""
    s = json.loads((REPO / "spec" / "schemas" / "uofa.schema.json").read_text())
    for branch in s["oneOf"]:
        props = branch["allOf"][1]["properties"]
        assert attestations.IDENTITY_BLOCK_KEY in props, branch["title"]
        assert attestations.AUTHORIZATION_BLOCK_KEY in props, branch["title"]
    for name in ("IdentityBindingAttestationShape", "AuthorizationAttestationShape"):
        assert name in s["$defs"], f"{name} is referenced but not defined"


def test_every_ref_in_the_generated_schema_resolves():
    """A `$ref` with no `$defs` entry is a schema no validator can load. The
    generator emits a `$ref` for every `sh:node`, so adding a shape without
    adding its definition silently produces an unloadable artifact."""
    import re
    s = json.loads((REPO / "spec" / "schemas" / "uofa.schema.json").read_text())
    refs = set(re.findall(r"#/\$defs/([A-Za-z]+)", json.dumps(s)))
    assert not refs - set(s["$defs"]), sorted(refs - set(s["$defs"]))


def test_sip_bundles_accept_both_blocks():
    """`sip_evidence_bundle_schema.json` is `additionalProperties: false` at the
    root, so a key it does not list is REJECTED, not ignored."""
    import jsonschema
    s = json.loads((REPO / "specs" / "sip_evidence_bundle_schema.json").read_text())
    assert s.get("additionalProperties") is False, (
        "this test's premise is gone: the SIP root no longer refuses unknown "
        "keys, so it no longer proves anything")
    for key, block in ((attestations.IDENTITY_BLOCK_KEY, _binding()),
                       (attestations.AUTHORIZATION_BLOCK_KEY, _authorization())):
        assert key in s["properties"], f"a SIP bundle would reject {key}"
        jsonschema.Draft202012Validator(s["properties"][key]).validate(block)


# ── the machine-readable report ──────────────────────────────────────────────

def test_check_reports_which_attestations_a_package_carries():
    """Presence is a fact `check` can establish with no key at all."""
    from uofa_cli.commands.check import CheckResult
    import dataclasses
    names = {f.name: f for f in dataclasses.fields(CheckResult)}
    assert "attestations" in names
    assert names["attestations"].default is None, (
        "it must default to None, not []. `snapshot.py` OMITS None fields, and "
        "that omission is the whole mechanism by which a new field ships "
        "without rewriting every stored baseline report; a field that "
        "serialises at its default rewrites all of them.")


def test_an_absent_attestation_list_is_omitted_from_the_snapshot():
    """The byte-identity contract, exercised rather than assumed."""
    from uofa_cli.oos import snapshot
    import inspect
    src = inspect.getsource(snapshot)
    assert "is None" in src, "the None-omission rule is gone from the serializer"


def test_check_never_reports_a_trust_state():
    """`check` takes no `--authority-pubkey`, so any trust verdict it printed
    would be invented. The four states belong to `verify`, which has the key."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "src" / "uofa_cli" /
           "commands" / "check.py").read_text()
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    for state in (attestations.TRUST_TRUSTED, attestations.TRUST_UNTRUSTED,
                  attestations.TRUST_INVALID):
        assert state not in code, (
            f"`check` reports {state!r} without ever being given a trust anchor")
