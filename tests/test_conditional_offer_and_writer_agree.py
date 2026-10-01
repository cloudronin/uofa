"""What is offered as a decision, and what is written as one, is what the shape
accepts.

Core SHACL takes a top-level `uofa:decision` of "Accepted" or "Not accepted" and
nothing else. Two places disagreed with it.

- **The vv40 and nasa-7009b extract prompts offered "Conditional".** Each
  prompt's task list says there is no third value -- "Emitting 'Conditional'
  fails schema validation" -- and then its output format offered it anyway, and
  the NASA prompt's rules said the outcome "MUST be exactly one of Accepted,
  Not accepted, or Conditional". A model following the more specific
  instruction wrote a package the shape rejects.
- **`read_sip_bundle` wrote a signed "Conditional" to the top level.** The SIP
  schema allows it as an engineer's decision and `uofa decision record --value
  conditional` records it, so a valid, signed input became a package failing
  the shape. The judgment is kept, verbatim, in the decision record, where no
  shape constrains the outcome; the top-level decision is left out, which the
  shape permits (`sh:maxCount 1`, no minimum).

The acceptable set is read from the shape, not written out here: a copy in the
test would pass against a shape that had moved.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pytest

from uofa_cli import integrity
from uofa_cli.commands import decision, sign as sign_cmd
from uofa_cli.interrogate import signing
from uofa_cli.readers.sip_bundle_reader import read_sip_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_SHAPES = REPO_ROOT / "packs/core/shapes/uofa_shacl.ttl"
PROMPTS = {
    "vv40": REPO_ROOT / "packs/vv40/prompts/vv40_extract_prompt.txt",
    "nasa-7009b": REPO_ROOT / "packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt",
}


def accepted_by_the_shape() -> set[str]:
    """The `sh:in` list on the core shape's `uofa:decision` property."""
    text = CORE_SHAPES.read_text(encoding="utf-8")
    block = re.search(r"sh:path uofa:decision ;(.*?)\]", text, re.S)
    assert block, "the core shape no longer constrains uofa:decision"
    values = re.search(r"sh:in \((.*?)\)", block.group(1), re.S)
    assert values, "the uofa:decision constraint no longer lists its values"
    return set(re.findall(r'"([^"]+)"', values.group(1)))


def offered_by(prompt: Path) -> set[str]:
    """Every outcome the prompt's output format or rules put on offer."""
    text = prompt.read_text(encoding="utf-8")
    offered: set[str] = set()
    for line in re.findall(r"^outcome:\s*(.+)$", text, re.M):
        offered |= {v.strip() for v in line.split(" or ")}
    for line in re.findall(r"MUST be exactly one of (.+?)\. ", text):
        offered |= set(re.findall(r'"([^"]+)"', line))
    return offered


def test_the_shape_accepts_two_outcomes():
    assert accepted_by_the_shape() == {"Accepted", "Not accepted"}


@pytest.mark.parametrize("pack", sorted(PROMPTS))
def test_the_prompt_offers_only_outcomes_the_shape_accepts(pack):
    offered = offered_by(PROMPTS[pack])
    assert offered, f"{pack}'s prompt offers no outcome at all"
    assert offered <= accepted_by_the_shape(), (
        f"{pack}'s prompt offers {sorted(offered - accepted_by_the_shape())}, "
        f"which the core shape rejects")


# ── the SIP reader ───────────────────────────────────────────────────────────

def _bundle() -> dict:
    return {
        "bundleId": "b", "sipVersion": "0.1.0", "schemaVersion": "sip-evidence-bundle/v0.1",
        "generatedAt": "2026-05-30T12:00:00Z",
        "subject": {"surrogateId": "s", "modelVersion": "1", "surrogateType": "PINN",
                    "modelFingerprint": "sha256:x", "adapterRef": "m:A"},
        "declaredScope": {"trainingEnvelope": {"dimensions": [{"name": "re", "min": 1.0, "max": 2.0}]},
                          "declaredPhysicsConstraint": []},
        "measurementProvenance": [{"measurementId": "m1", "producedBy": {"library": "numpy", "version": "1.26"}}],
        "measurements": {
            "referenceResiduals": [{"quantityOfInterest": "cl", "statistics": {"count": 10, "mean": 0.01, "rms": 0.02, "max": 0.05}}],
            "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": True},
            "physicsConstraintResidual": [],
            "uqCalibration": {"surrogateUQMethod": "conformal-prediction", "empiricalCoverage": 0.9, "nominalCoverage": 0.9},
        },
        "provenance": {"activity": {"id": "sip:run", "type": "prov:Activity"}},
        "completeness": {"fieldsPresent": ["referenceResiduals"], "fieldsDeliberatelyOmitted": []},
    }


def _decided(tmp_path, value: str) -> dict:
    """A measured, signed bundle carrying a signed engineer decision, read."""
    sip, eng = tmp_path / "sip.key", tmp_path / "eng.key"
    integrity.generate_keypair(sip)
    integrity.generate_keypair(eng)
    pkg = tmp_path / "bundle.json"
    pkg.write_text(json.dumps(_bundle()), encoding="utf-8")
    signing.sign_measurement(pkg, sip)
    assert decision.run(argparse.Namespace(
        decision_cmd="record", file=pkg, criterion="Cl within 3% over envelope",
        value=value, rationale="within tolerance, on the stated conditions",
        decided_at="2026-05-30T00:00:00Z", actor="https://uofa.net/org/demo-reviewer",
        append=False, output=None)) == 0
    parser = argparse.ArgumentParser()
    sign_cmd.add_arguments(parser)
    assert sign_cmd.run(parser.parse_args(
        [str(pkg), "--key", str(eng), "--as", "reviewer"])) == 0
    return read_sip_bundle(pkg, measurement_pubkey=sip.with_suffix(".pub"),
                           decision_pubkey=eng.with_suffix(".pub"))


def test_a_conditional_decision_is_kept_and_not_written_where_the_shape_forbids_it(tmp_path):
    doc = _decided(tmp_path, "conditional")
    assert doc["hasDecisionRecord"]["outcome"] == "Conditional", "the judgment, verbatim"
    assert doc.get("decision") in accepted_by_the_shape() | {None}
    assert "decision" not in doc


@pytest.mark.parametrize("value, outcome", [("accepted", "Accepted"),
                                            ("not-accepted", "Not accepted")])
def test_an_accepted_or_not_accepted_decision_is_still_written_at_the_top(tmp_path, value, outcome):
    doc = _decided(tmp_path, value)
    assert doc["decision"] == outcome
    assert doc["hasDecisionRecord"]["outcome"] == outcome
