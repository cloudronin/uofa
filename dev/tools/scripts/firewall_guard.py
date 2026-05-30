#!/usr/bin/env python3
"""The interrogation firewall guard (CI / release_check).

SIP measures; it never judges. This guard imports the ONE forbidden-token list
(``uofa_cli.interrogate.forbidden.FORBIDDEN_TOKENS``) — it is a Python script,
not a raw grep, precisely so it can never drift from the schema and tests it
defends. It fails (non-zero) when any of these hold:

  1. the SIP evidence-bundle schema *whitelists* a forbidden property name;
  2. the schema's root ``propertyNames`` denylist has drifted from FORBIDDEN_TOKENS;
  3. any committed SIP bundle carries a forbidden property name;
  4. the wheel does not force-include ``specs/`` (so the schema — and thus the
     firewall's schema layer — would be unreachable after a real pip install).

Run: ``python dev/tools/scripts/firewall_guard.py``. Wired into ``make all``
(adding it to ``release_check.py`` is a recommended follow-up). See AGENTS.md §12.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uofa_cli.interrogate.forbidden import (  # noqa: E402
    FORBIDDEN_TOKENS,
    find_forbidden_in_measurement_region,
)

SCHEMA_PATH = REPO_ROOT / "specs" / "sip_evidence_bundle_schema.json"


def _declared_property_names(node, acc: set[str]) -> None:
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            acc.update(props.keys())
        for value in node.values():
            _declared_property_names(value, acc)
    elif isinstance(node, list):
        for item in node:
            _declared_property_names(item, acc)


def schema_violations(schema: dict) -> list[str]:
    """Violations in the SIP schema under the signature-scoped firewall (A5).

    Checks: (1) no forbidden token is whitelisted as a measurement-region
    property; (2) the measurement-region denylist (the provenance freeform
    object) stays in lockstep with FORBIDDEN_TOKENS; (3) the engineerDecision
    block exists and is EXEMPT from the denylist (decision content lives there,
    governed by its signature, not the token check).
    """
    violations: list[str] = []
    forbidden = set(FORBIDDEN_TOKENS)
    properties = schema.get("properties", {})

    # (1) No forbidden token whitelisted anywhere in the schema. (engineerDecision's
    # own sub-properties are decidedBy/decisionValue/... — none are forbidden
    # tokens — so scanning the whole schema stays clean and needs no special-case.)
    declared: set[str] = set()
    _declared_property_names(schema, declared)
    for name in sorted(declared & forbidden):
        violations.append(f"schema whitelists forbidden property name: {name!r}")

    # (2) Measurement-region denylist lockstep (checked on the provenance object).
    prov = properties.get("provenance", {})
    enum = prov.get("propertyNames", {}).get("not", {}).get("enum") if isinstance(prov, dict) else None
    if enum is None:
        violations.append("measurement-region propertyNames denylist is missing (properties.provenance)")
    elif set(enum) != forbidden:
        violations.append(
            f"measurement-region denylist has drifted from FORBIDDEN_TOKENS "
            f"(missing={sorted(forbidden - set(enum))}, extra={sorted(set(enum) - forbidden)})"
        )

    # (3) engineerDecision present and exempt (no denylist) — signature-governed.
    engineer_decision = properties.get("engineerDecision")
    if not isinstance(engineer_decision, dict):
        violations.append("schema is missing the engineerDecision block (Addendum A4)")
    elif "propertyNames" in engineer_decision:
        violations.append(
            "engineerDecision must be EXEMPT from the denylist (no propertyNames) — "
            "it is governed by the signature check, not a token match (A5)"
        )

    return violations


def bundle_violations(bundle: dict, label: str = "<bundle>") -> list[str]:
    """Forbidden decision content in the measurement region of a SIP bundle.

    Signature-scoped (Addendum A5): the top-level engineerDecision block is
    exempt (governed by its signature); decision content anywhere else is a
    breach.
    """
    return [
        f"{label}: forbidden field {token!r} at {path}"
        for path, token in find_forbidden_in_measurement_region(bundle)
    ]


def force_include_violations(pyproject: dict) -> list[str]:
    """Verify the wheel force-includes specs/ so the schema ships to real users."""
    force_include = (
        pyproject.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
        .get("force-include", {})
    )
    if "specs" not in force_include:
        return [
            "pyproject [tool.hatch.build.targets.wheel.force-include] does not map "
            "'specs' — the SIP schema would be unreachable after a non-editable "
            "pip install, silently disabling the firewall's schema layer."
        ]
    return []


def _iter_committed_bundles() -> list[Path]:
    roots = [REPO_ROOT / "packs" / "surrogate" / "examples",
             REPO_ROOT / "tests" / "fixtures" / "interrogate"]
    found: list[Path] = []
    for root in roots:
        if root.is_dir():
            for path in root.rglob("*.json"):
                try:
                    obj = json.loads(path.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    continue
                if isinstance(obj, dict) and str(obj.get("schemaVersion", "")).startswith("sip-evidence-bundle"):
                    found.append(path)
    return found


def main() -> int:
    violations: list[str] = []

    if not SCHEMA_PATH.is_file():
        print(f"FIREWALL GUARD: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        return 2
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    violations += schema_violations(schema)

    for bundle_path in _iter_committed_bundles():
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        violations += bundle_violations(bundle, label=str(bundle_path.relative_to(REPO_ROOT)))

    pyproject_path = REPO_ROOT / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            import tomllib
        except ModuleNotFoundError:  # py3.10
            import tomli as tomllib  # type: ignore[no-redef]
        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        violations += force_include_violations(pyproject)

    if violations:
        print("FIREWALL GUARD: VIOLATIONS DETECTED", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("FIREWALL GUARD: ok — SIP measures, it never judges.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
