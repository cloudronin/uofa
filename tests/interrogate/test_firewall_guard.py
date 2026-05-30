"""Firewall guard self-tests (Step 5).

The guard (dev/tools/scripts/firewall_guard.py) is the CI/release enforcement
of the firewall. These tests prove it (a) passes on the real, clean repo and
(b) actually catches each violation class — schema whitelist leak, denylist
drift, a poisoned bundle, and a wheel that drops the specs/ force-include.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD_PATH = REPO_ROOT / "dev" / "tools" / "scripts" / "firewall_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("firewall_guard", GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_guard()


def _real_schema() -> dict:
    return json.loads((REPO_ROOT / "specs" / "sip_evidence_bundle_schema.json").read_text())


class TestSchemaChecks:
    def test_real_schema_is_clean(self):
        assert guard.schema_violations(_real_schema()) == []

    def test_whitelisting_a_forbidden_field_is_caught(self):
        schema = _real_schema()
        schema["properties"]["verdict"] = {"type": "string"}
        violations = guard.schema_violations(schema)
        assert any("verdict" in v for v in violations)

    def test_denylist_drift_is_caught(self):
        # Addendum A5: the denylist is scoped to the measurement region now.
        schema = _real_schema()
        schema["properties"]["provenance"]["propertyNames"]["not"]["enum"] = list(FORBIDDEN_TOKENS)[:-1]
        violations = guard.schema_violations(schema)
        assert any("drift" in v.lower() for v in violations)

    def test_engineer_decision_under_denylist_is_caught(self):
        # The engineerDecision block must stay EXEMPT (signature-governed).
        schema = _real_schema()
        schema["properties"]["engineerDecision"]["propertyNames"] = {"not": {"enum": ["accepted"]}}
        violations = guard.schema_violations(schema)
        assert any("engineerDecision must be EXEMPT" in v for v in violations)

    def test_missing_engineer_decision_block_is_caught(self):
        schema = _real_schema()
        del schema["properties"]["engineerDecision"]
        violations = guard.schema_violations(schema)
        assert any("engineerDecision" in v for v in violations)


class TestBundleChecks:
    def test_poisoned_bundle_is_caught(self):
        bundle = {"schemaVersion": "sip-evidence-bundle/v0.1", "measurements": {"verdict": "PASS"}}
        violations = guard.bundle_violations(bundle, label="poison")
        assert any("verdict" in v for v in violations)

    def test_clean_bundle_passes(self):
        bundle = {"schemaVersion": "sip-evidence-bundle/v0.1",
                  "parentModelSnapshot": {"parentDecision": "Accepted"}}
        assert guard.bundle_violations(bundle) == []


class TestForceIncludeCheck:
    def test_missing_specs_force_include_is_caught(self):
        pyproject = {"tool": {"hatch": {"build": {"targets": {"wheel": {"force-include": {"packs": "x"}}}}}}}
        assert guard.force_include_violations(pyproject) != []

    def test_specs_force_include_passes(self):
        pyproject = {"tool": {"hatch": {"build": {"targets": {"wheel": {"force-include": {"specs": "x"}}}}}}}
        assert guard.force_include_violations(pyproject) == []


def test_guard_main_passes_on_real_repo():
    assert guard.main() == 0
