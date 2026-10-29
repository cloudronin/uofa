"""Surrogate governance loop, uofa side: U1 to U4 acceptance.

U1  W-SURR-05 fires on the 45 NACA entrance annotations and is quiet on the
    40 fully developed points (which carry the same observation fields, so the
    silence is a judgement about the numbers).
U2  W-SURR-06 fires on the Lewis 35A gravity-on case at the three downstream
    stations at theta = 0.10 and is quiet on gravity-off at every station.
U3  An external WeakenerAnnotation (source external, attributed to a software
    agent with name and version, no Disposition) passes the shapes, is listed
    by `uofa rules --format json` with its source, and a sealed package
    verifies from a clean directory. Each shape gate is failed on purpose once.
U4  A recommendedAction is never read as a Disposition: the firing is reported
    undispositioned until a Disposition node's dispositionOf names it.

The rule firings are counted from the engine's deductions (the derived markers
_closureOutsideValidatedRange / _omittedMechanismMaterial), because an
external annotation already carries its patternId and severity in the data and
re-asserting those leaves no new triple.

Skipped when the Jena engine (Java + built JAR) is unavailable.
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands import rules as rules_mod
from uofa_cli.commands import shacl as shacl_mod
from uofa_cli.commands import sign as sign_mod
from uofa_cli.commands import verify as verify_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "packs" / "surrogate" / "examples" / "physmap"
NACA = EXAMPLES / "naca-entrance" / "uofa-surrogate-naca-entrance.jsonld"
LEWIS_ON = EXAMPLES / "lewis-35a-gravity-on" / "uofa-surrogate-lewis-35a-gravity-on.jsonld"
LEWIS_OFF = EXAMPLES / "lewis-35a-gravity-off" / "uofa-surrogate-lewis-35a-gravity-off.jsonld"
PUBKEY = EXAMPLES / "keys" / "physmap-examples.pub"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "weakeners"

SURR = "https://uofa.net/vocab/surrogate#"
MARKER_05 = f"{SURR}_closureOutsideValidatedRange"
MARKER_06 = f"{SURR}_omittedMechanismMaterial"
PACKS = ["surrogate", "disposition"]


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:  # noqa: BLE001 - any failure means "no engine here"
        return False
    return paths.jar_path().exists()


needs_engine = pytest.mark.skipif(not _engine_available(),
                                  reason="Jena engine (Java + built JAR) not available")


# ── helpers ───────────────────────────────────────────────────────────────────

def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(tmp_path: Path, name: str, doc: dict) -> Path:
    out = tmp_path / name
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return out


def _deductions(path: Path) -> str:
    args = argparse.Namespace(file=path, rules=None, context=None, build=False, raw=False,
                              format="ntriples", output=None, active_packs=["surrogate"])
    result = rules_mod.run_structured(args)
    assert result.returncode == 0, result.raw_stderr
    return result.raw_stdout


def _marked_nodes(path: Path, marker: str) -> list[str]:
    return [line.split(" ", 1)[0].strip("<>")
            for line in _deductions(path).splitlines() if f"<{marker}>" in line]


def _summary_firings(path: Path) -> dict[str, int]:
    args = argparse.Namespace(file=path, rules=None, context=None, build=False, raw=False,
                              format="summary", output=None, active_packs=["surrogate"])
    result = rules_mod.run_structured(args)
    assert result.returncode == 0, result.raw_stderr
    return {f["patternId"]: f["hits"] for f in result.firings}


def _rules_json(path: Path) -> dict:
    """The production path: the CLI itself, as a downstream tool would call it."""
    proc = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "rules", str(path), "--pack", "surrogate", "--format", "json"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _shacl(path: Path) -> shacl_mod.ShaclResult:
    args = argparse.Namespace(file=path, raw=False, active_packs=PACKS)
    return shacl_mod.run_structured(args)


def _verify(path: Path, pubkey: Path, capsys) -> tuple[int, str]:
    args = argparse.Namespace(file=path, pubkey=pubkey, context=None,
                              authority_pubkey=None, decision_pubkey=None)
    rc = verify_mod.run(args)
    return rc, capsys.readouterr().out


def _external_annotations(doc: dict) -> list[dict]:
    return [w for w in doc["hasWeakener"] if w.get("source") == "external"]


# ── U1: W-SURR-05 on the NACA export ──────────────────────────────────────────

@needs_engine
class TestU1ClosureOutsideValidatedRange:
    def test_fires_on_the_45_entrance_annotations(self):
        marked = _marked_nodes(NACA, MARKER_05)
        assert len(marked) == 45
        assert set(marked) == {w["id"] for w in _external_annotations(_load(NACA))}
        assert _summary_firings(NACA).get("W-SURR-05") == 45

    def test_quiet_on_the_40_fully_developed_points_which_carry_the_observation(self):
        doc = _load(NACA)
        quiet = [f for f in doc[f"{SURR}applicabilityFactor"] if f["factorStatus"] == "quiet"]
        assert len(quiet) == 40
        # Not vacuous: every quiet point carries the closure, the bound and a value
        # the rule could have judged. It judged them inside the range.
        for f in quiet:
            assert f[f"{SURR}closureId"] == "gnielinski-1976"
            assert f[f"{SURR}observedValue"] >= f[f"{SURR}validatedMin"]
        marked = set(_marked_nodes(NACA, MARKER_05))
        assert not marked & {f["id"] for f in quiet}

    def test_the_only_pattern_on_the_naca_package_is_w_surr_05(self):
        # W-SURR-03 (training envelope) stays silent: x/D is not a surrogate input.
        assert _summary_firings(NACA) == {"W-SURR-05": 45}

    @pytest.mark.parametrize("variant,fires", [("positive", True), ("negative", False), ("boundary", False)])
    def test_rule_fixture(self, variant, fires):
        marked = _marked_nodes(FIXTURES / "W-SURR-05" / f"{variant}.jsonld", MARKER_05)
        assert bool(marked) is fires

    def test_fires_above_an_upper_bound_too(self, tmp_path):
        doc = _load(FIXTURES / "W-SURR-05" / "negative.jsonld")
        ann = doc["hasWeakener"]
        del ann[f"{SURR}validatedMin"]
        ann[f"{SURR}validatedMax"] = 5.0   # observed 12 > 5
        assert len(_marked_nodes(_write(tmp_path, "above.jsonld", doc), MARKER_05)) == 1


# ── U2: W-SURR-06 on Lewis 35A ────────────────────────────────────────────────

@needs_engine
class TestU2OmittedMechanismMaterial:
    def test_fires_at_the_three_downstream_stations_with_gravity_on(self):
        marked = _marked_nodes(LEWIS_ON, MARKER_06)
        assert len(marked) == 3
        stations = {m.rsplit("/", 1)[1] for m in marked}
        assert stations == {"xd67p55", "xd101p69", "xd135p84"}
        assert _summary_firings(LEWIS_ON) == {"W-SURR-06": 3}

    def test_quiet_below_the_threshold_with_gravity_on(self):
        doc = _load(LEWIS_ON)
        below = [f for f in doc[f"{SURR}applicabilityFactor"] if f["factorStatus"] == "quiet"]
        assert len(below) == 6   # nine comparable stations, three at or above theta
        for f in below:
            assert f[f"{SURR}observedValue"] > f[f"{SURR}calibrationMax"]      # active
            assert f[f"{SURR}materiality"] < f[f"{SURR}materialityThreshold"]  # not material
        assert not set(_marked_nodes(LEWIS_ON, MARKER_06)) & {f["id"] for f in below}

    def test_quiet_at_every_station_with_gravity_off(self):
        doc = _load(LEWIS_OFF)
        observed = [f for f in doc[f"{SURR}applicabilityFactor"] if f"{SURR}materiality" in f]
        assert len(observed) == 9 and all(f[f"{SURR}materiality"] == 0.0 for f in observed)
        assert _marked_nodes(LEWIS_OFF, MARKER_06) == []
        assert _summary_firings(LEWIS_OFF) == {}

    def test_threshold_is_recorded_as_illustrative(self):
        for path in (LEWIS_ON, LEWIS_OFF):
            doc = _load(path)
            nodes = _external_annotations(doc) + [
                f for f in doc[f"{SURR}applicabilityFactor"] if f"{SURR}materiality" in f]
            assert nodes
            for n in nodes:
                assert n[f"{SURR}materialityThreshold"] == 0.10
                assert n[f"{SURR}materialityThresholdStatus"] == "illustrative"

    @pytest.mark.parametrize("variant,fires", [("positive", True), ("negative", False), ("boundary", True)])
    def test_rule_fixture(self, variant, fires):
        marked = _marked_nodes(FIXTURES / "W-SURR-06" / f"{variant}.jsonld", MARKER_06)
        assert bool(marked) is fires

    def test_quiet_when_the_group_is_inside_the_window_however_material(self, tmp_path):
        doc = _load(FIXTURES / "W-SURR-06" / "positive.jsonld")
        doc["hasWeakener"][f"{SURR}observedValue"] = 0.0   # Ri inside [0, 0]: inactive
        assert _marked_nodes(_write(tmp_path, "inactive.jsonld", doc), MARKER_06) == []


# ── U3: the external annotation rule ─────────────────────────────────────────

class TestU3ShapesAcceptExternalAnnotations:
    @pytest.mark.parametrize("path", [NACA, LEWIS_ON, LEWIS_OFF], ids=["naca", "lewis-on", "lewis-off"])
    def test_physmap_derived_package_conforms(self, path):
        result = _shacl(path)
        assert result.conforms, [v.get("message") for v in result.violations]

    def test_annotations_arrive_with_no_disposition(self):
        doc = _load(NACA)
        assert not any("Disposition" in (n.get("type") or "") for n in _walk(doc))
        for w in _external_annotations(doc):
            assert w["wasAttributedTo"] == "https://github.com/cloudronin/physmap"
        agent = doc["hasValidationResult"]["wasAttributedTo"]
        assert agent["type"] == "prov:SoftwareAgent"
        assert agent["name"] == "physmap" and agent["version"]

    # The gate, failed on purpose, once per clause.
    def _mutated(self, tmp_path, mutate) -> Path:
        doc = _load(NACA)
        mutate(doc)
        return _write(tmp_path, "mutant.jsonld", doc)

    def test_fails_without_attribution(self, tmp_path):
        def strip(doc):
            del doc["hasWeakener"][0]["wasAttributedTo"]
        assert not _shacl(self._mutated(tmp_path, strip)).conforms

    def test_fails_when_the_agent_has_no_version(self, tmp_path):
        def strip(doc):
            del doc["hasValidationResult"]["wasAttributedTo"]["version"]
        assert not _shacl(self._mutated(tmp_path, strip)).conforms

    def test_fails_when_the_agent_has_no_name(self, tmp_path):
        def strip(doc):
            del doc["hasValidationResult"]["wasAttributedTo"]["name"]
        assert not _shacl(self._mutated(tmp_path, strip)).conforms

    def test_fails_without_a_justification(self, tmp_path):
        def strip(doc):
            del doc["hasWeakener"][0]["justification"]
        assert not _shacl(self._mutated(tmp_path, strip)).conforms

    def test_fails_on_a_misspelt_source(self, tmp_path):
        def spell(doc):
            doc["hasWeakener"][0]["source"] = "External"
        assert not _shacl(self._mutated(tmp_path, spell)).conforms

    def test_fails_on_a_recommendation_outside_the_five_classes(self, tmp_path):
        def bad(doc):
            doc["hasWeakener"][0]["recommendedAction"] = "deploy"
        assert not _shacl(self._mutated(tmp_path, bad)).conforms

    def test_an_annotation_with_no_source_needs_no_attribution(self, tmp_path):
        def plain(doc):
            del doc["hasWeakener"][0]["source"]
            del doc["hasWeakener"][0]["wasAttributedTo"]
        assert _shacl(self._mutated(tmp_path, plain)).conforms


@needs_engine
class TestU3RulesJsonListsExternalFirings:
    def test_naca_firings_carry_the_source_field(self):
        out = _rules_json(NACA)
        assert out["summary"]["by_source"] == {"external": 45}
        assert out["summary"]["total_firings"] == 45
        (firing,) = out["firings"]
        assert firing["patternId"] == "W-SURR-05"
        assert firing["source"] == "external"
        assert firing["hits_by_source"] == {"external": 45}
        assert len(firing["annotations"]) == 45
        assert all(a["source"] == "external" for a in firing["annotations"])
        assert all(a["attributed_to"] == "https://github.com/cloudronin/physmap"
                   for a in firing["annotations"])

    def test_lewis_firings_name_the_three_stations(self):
        out = _rules_json(LEWIS_ON)
        (firing,) = out["firings"]
        assert firing["patternId"] == "W-SURR-06" and firing["hits"] == 3
        assert {a["affected_node"].rsplit("/", 1)[1] for a in firing["annotations"]} == {
            "xd67p55", "xd101p69", "xd135p84"}
        assert _rules_json(LEWIS_OFF)["firings"] == []

    def test_engine_firings_are_labelled_engine(self, tmp_path):
        # A package with no authored annotations: everything is the engine's.
        doc = _load(FIXTURES / "W-SURR-05" / "negative.jsonld")
        del doc["hasWeakener"]
        del doc["hasValidationResult"]   # W-SI-02 fires: a core, engine-inferred weakener
        out = _rules_json(_write(tmp_path, "engine.jsonld", doc))
        assert out["firings"], "expected a core weakener to fire"
        assert all(f["source"] == "engine" for f in out["firings"])
        assert "external" not in out["summary"]["by_source"]
        assert out["summary"]["undispositioned"] == 0


class TestU3SealedPackageVerifiesElsewhere:
    def test_shipped_seal_verifies_from_a_clean_directory(self, tmp_path, capsys):
        # A fresh directory with nothing beside the file: no sibling context, no keys.
        elsewhere = tmp_path / "second-machine"
        elsewhere.mkdir()
        copied = elsewhere / NACA.name
        shutil.copy(NACA, copied)
        pub = elsewhere / "physmap-examples.pub"
        shutil.copy(PUBKEY, pub)
        rc, out = _verify(copied, pub, capsys)
        assert rc == 0, out
        assert "Measurement hash match" in out and "Measurement signature valid" in out

    def test_tampering_with_an_external_annotation_breaks_the_seal(self, tmp_path, capsys):
        doc = _load(NACA)
        doc["hasWeakener"][0][f"{SURR}observedValue"] = 12.0   # now inside the range
        tampered = _write(tmp_path, NACA.name, doc)
        rc, out = _verify(tampered, PUBKEY, capsys)
        assert rc == 1, out

    def test_sign_then_verify_round_trip_with_a_fresh_key(self, tmp_path, signing_keypair, capsys):
        key, pub = signing_keypair
        doc = _load(LEWIS_ON)
        doc["hash"], doc["signature"] = "sha256:" + "0" * 64, "ed25519:" + "0" * 128
        here = tmp_path / "author"
        here.mkdir()
        unsigned = _write(here, LEWIS_ON.name, doc)
        rc = sign_mod.run(argparse.Namespace(file=unsigned, key=key, context=None, output=None,
                                             roles="issuer"))
        assert rc == 0
        elsewhere = tmp_path / "second-machine"
        elsewhere.mkdir()
        copied = elsewhere / LEWIS_ON.name
        shutil.copy(unsigned, copied)
        capsys.readouterr()
        rc, out = _verify(copied, pub, capsys)
        assert rc == 0, out


# ── U4: recommendation, not decision ─────────────────────────────────────────

def _walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)


@needs_engine
class TestU4RecommendationIsNotADisposition:
    def test_every_naca_annotation_recommends_and_none_is_dispositioned(self):
        out = _rules_json(NACA)
        (firing,) = out["firings"]
        assert firing["recommended_actions"] == {"characterize-region": 45}
        assert firing["disposition"] == {"undispositioned": 45, "dispositioned": 0}
        assert all(a["recommendedAction"] == "characterize-region" for a in firing["annotations"])
        assert all(a["disposition"] == "undispositioned" for a in firing["annotations"])
        assert out["summary"]["undispositioned"] == 45

    def test_a_disposition_node_naming_the_annotation_dispositions_it(self, tmp_path):
        # The positive control: the state CAN change, and only through a Disposition.
        doc = _load(NACA)
        target = doc["hasWeakener"][0]["id"]
        doc["hasDisposition"] = {
            "id": "https://uofa.net/surrogate/physmap/naca-entrance/disposition/1",
            "type": "Disposition",
            "actionClass": "restrict-cou",
            "actionParameters": "exclude x/D < 10 from the context of use",
            "dispositionOf": target,
        }
        out = _rules_json(_write(tmp_path, "one-dispositioned.jsonld", doc))
        (firing,) = out["firings"]
        assert firing["disposition"] == {"undispositioned": 44, "dispositioned": 1}
        by_id = {a["id"]: a["disposition"] for a in firing["annotations"]}
        assert by_id[target] == doc["hasDisposition"]["id"]
        assert out["summary"]["undispositioned"] == 44

    def test_a_disposition_that_names_no_annotation_dispositions_nothing(self, tmp_path):
        # PhysMAP's current export shape: one Disposition per point, no link to the
        # annotation. It is a disposition of nothing until dispositionOf says which.
        doc = _load(NACA)
        doc["hasDisposition"] = {
            "id": "https://uofa.net/surrogate/physmap/naca-entrance/disposition/unlinked",
            "type": "Disposition",
            "actionClass": "characterize-region",
        }
        out = _rules_json(_write(tmp_path, "unlinked.jsonld", doc))
        assert out["firings"][0]["disposition"] == {"undispositioned": 45, "dispositioned": 0}

    def test_a_recommendation_matching_an_action_class_is_still_not_a_disposition(self, tmp_path):
        doc = _load(NACA)
        for w in doc["hasWeakener"]:
            w["recommendedAction"] = "accept-residual-risk"
        out = _rules_json(_write(tmp_path, "recommend-accept.jsonld", doc))
        (firing,) = out["firings"]
        assert firing["recommended_actions"] == {"accept-residual-risk": 45}
        assert firing["disposition"]["undispositioned"] == 45


class TestAuthoredAnnotationReader:
    """The reader `rules --format json` uses, in isolation."""

    def test_reads_source_recommendation_and_disposition_state(self):
        doc = _load(NACA)
        records = rules_mod.authored_annotations(doc)
        assert len(records) == 45
        assert {r["source"] for r in records} == {"external"}
        assert {r["disposition"] for r in records} == {"undispositioned"}
        assert {r["recommendedAction"] for r in records} == {"characterize-region"}

    def test_an_authored_annotation_without_a_source_is_package(self):
        doc = copy.deepcopy(_load(NACA))
        del doc["hasWeakener"][0]["source"]
        records = rules_mod.authored_annotations(doc)
        assert records[0]["source"] == "package"
        assert all(r["source"] == "external" for r in records[1:])

    def test_merge_keeps_engine_and_authored_hits_apart(self):
        engine = [{"patternId": "W-SI-02", "severity": "High", "hits": 2, "description": "",
                   "affected_nodes": ["https://x/pkg"], "escalation_sources": []}]
        authored = [{"id": "https://x/a1", "patternId": "W-SURR-05", "severity": "High",
                     "affected_node": "https://x/d1", "description": "", "source": "external",
                     "attributed_to": "https://x/agent", "recommendedAction": "",
                     "disposition": "undispositioned"}]
        merged = rules_mod.merge_authored_firings(engine, authored)
        by_pid = {m["patternId"]: m for m in merged}
        assert by_pid["W-SI-02"]["source"] == "engine" and "disposition" not in by_pid["W-SI-02"]
        assert by_pid["W-SURR-05"]["source"] == "external"
        assert by_pid["W-SURR-05"]["disposition"] == {"undispositioned": 1, "dispositioned": 0}

    def test_merge_marks_a_pattern_with_both_kinds_mixed(self):
        engine = [{"patternId": "W-SURR-05", "severity": "High", "hits": 1, "description": "",
                   "affected_nodes": [], "escalation_sources": []}]
        authored = [{"id": "https://x/a1", "patternId": "W-SURR-05", "severity": "High",
                     "affected_node": "", "description": "", "source": "external",
                     "attributed_to": "", "recommendedAction": "", "disposition": "undispositioned"}]
        (merged,) = rules_mod.merge_authored_firings(engine, authored)
        assert merged["source"] == "mixed" and merged["hits"] == 2
