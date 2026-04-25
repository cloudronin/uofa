"""Prompt-template registry.

Phase 1 ships one template (W-AR-05). Phase 2 scales by adding keys to
``_REGISTRY`` and modules under ``prompts/``.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType

_REGISTRY: dict[str, str] = {
    "W-AR-01": "uofa_cli.adversarial.prompts.d1_undermining",
    "W-AR-02": "uofa_cli.adversarial.prompts.d2_rebutting",
    "W-AR-03": "uofa_cli.adversarial.prompts.d3_undercutting_inference",
    "W-AR-04": "uofa_cli.adversarial.prompts.d3_undercutting_model",
    "W-AR-05": "uofa_cli.adversarial.prompts.d3_undercutting_inference",
    "W-EP-01": "uofa_cli.adversarial.prompts.epistemic",
    "W-EP-02": "uofa_cli.adversarial.prompts.epistemic",
    "W-EP-03": "uofa_cli.adversarial.prompts.epistemic",
    "W-EP-04": "uofa_cli.adversarial.prompts.epistemic",
    "W-AL-01": "uofa_cli.adversarial.prompts.aleatory",
    "W-AL-02": "uofa_cli.adversarial.prompts.aleatory",
    "W-ON-01": "uofa_cli.adversarial.prompts.ontological",
    "W-ON-02": "uofa_cli.adversarial.prompts.ontological",
    "W-SI-01": "uofa_cli.adversarial.prompts.structural",
    "W-SI-02": "uofa_cli.adversarial.prompts.structural",
    "W-CON-01": "uofa_cli.adversarial.prompts.consistency",
    "W-CON-02": "uofa_cli.adversarial.prompts.consistency",
    "W-CON-03": "uofa_cli.adversarial.prompts.consistency",
    "W-CON-04": "uofa_cli.adversarial.prompts.consistency",
    "W-CON-05": "uofa_cli.adversarial.prompts.consistency",
    "W-PROV-01": "uofa_cli.adversarial.prompts.provenance",
    "COMPOUND-01": "uofa_cli.adversarial.prompts.compound",
    "COMPOUND-03": "uofa_cli.adversarial.prompts.compound",
}

_MOCK_FIXTURE_ENV = "UOFA_ADVERSARIAL_MOCK_FIXTURE"


class TemplateNotFoundError(Exception):
    """Raised when no prompt template exists for a weakener id."""


def get_template(weakener_id: str) -> ModuleType:
    """Return the prompt-template module for *weakener_id*."""
    mod_path = _REGISTRY.get(weakener_id)
    if not mod_path:
        raise TemplateNotFoundError(
            f"No Phase 1 prompt template for {weakener_id!r}. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return importlib.import_module(mod_path)


def mock_response(params: dict) -> str:
    """Return a known-good JSON-LD package string for dry-run / unit tests.

    Looks for a fixture path in ``params['mock_fixture']``, then in the
    ``UOFA_ADVERSARIAL_MOCK_FIXTURE`` env var, then falls back to the
    test fixture shipped with the package.
    """
    import os

    fixture = params.get("mock_fixture") or os.environ.get(_MOCK_FIXTURE_ENV)
    if fixture:
        return Path(fixture).read_text()

    # Fallback: minimal inline package. Only used if no fixture is configured.
    return json.dumps(_minimal_mock_package(), indent=2)


def _minimal_mock_package() -> dict:
    """A tiny SHACL-passing synthetic package for emergency fallback."""
    from uofa_cli.excel_constants import CONTEXT_URL

    return {
        "@context": CONTEXT_URL,
        "id": "https://uofa.net/synth/mock-fallback",
        "type": ["UnitOfAssurance", "uofa:SyntheticAdversarialSample"],
        "synthetic": True,
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "bindsRequirement": "https://uofa.net/synth/req/mock",
        "hasContextOfUse": {
            "id": "https://uofa.net/synth/cou/mock",
            "type": "ContextOfUse",
            "name": "Mock COU",
            "deviceClass": "Class II",
            "modelInfluence": "Medium",
            "decisionConsequence": "High",
        },
        "hasValidationResult": [
            {
                "id": "https://uofa.net/synth/validation/mock-no-comparator",
                "type": "ValidationResult",
                "name": "Mock validation without comparator",
            }
        ],
        "generatedAtTime": "2026-04-19T00:00:00Z",
        "hash": "sha256:" + "0" * 64,
        "signature": "ed25519:" + "0" * 128,
        "hasDecisionRecord": {
            "id": "https://uofa.net/synth/decision/mock",
            "type": "DecisionRecord",
            "actor": "https://uofa.net/synth/actor/mock",
            "outcome": "Accepted",
            "rationale": "Mock decision",
            "decidedAt": "2026-04-19T00:00:00Z",
        },
    }
