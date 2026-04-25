"""Prompt-template registry.

Phase 1 ships one confirm_existing template (W-AR-05). Phase 2 adds:

- 22 more confirm_existing templates (one per shipped UofA pattern)
- 23 gap_probe templates dispatched by ``source_taxonomy`` prefix
- 10 negative_control templates (single ``negative_controls`` module)
- 6 interaction templates (single ``multi_target`` module)

confirm_existing / interaction specs route by ``target_weakener``.
gap_probe specs route by the first two segments of ``source_taxonomy``
(e.g., ``gohar/evidence_validity/data-drift`` → ``gohar/evidence_validity``).
negative_control specs route via the sentinel ``"control/none"``.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import ModuleType

#: Maps target_weakener IDs to prompt-template modules.
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

#: Maps source_taxonomy prefix (taxonomy/category) to prompt-template modules
#: for gap_probe specs. Modules dispatch internally by the leaf sub-type.
_GAP_PROBE_REGISTRY: dict[str, str] = {
    "gohar/evidence_validity": "uofa_cli.adversarial.prompts.evidence_validity",
    "gohar/requirements": "uofa_cli.adversarial.prompts.requirements_engineering",
    "gohar/contextual": "uofa_cli.adversarial.prompts.contextual",
    "greenwell/sufficiency": "uofa_cli.adversarial.prompts.logical_fallacies",
    "clarissa-machinery/workflow": "uofa_cli.adversarial.prompts.clarissa_machinery",
}

#: Sentinel module path for negative_control specs.
_NEGATIVE_CONTROL_MODULE = "uofa_cli.adversarial.prompts.negative_controls"

_MOCK_FIXTURE_ENV = "UOFA_ADVERSARIAL_MOCK_FIXTURE"


class TemplateNotFoundError(Exception):
    """Raised when no prompt template exists for a weakener id or spec."""


def get_template(weakener_id: str) -> ModuleType:
    """Return the prompt-template module for *weakener_id*.

    confirm_existing / interaction call site. For gap_probe and
    negative_control specs use :func:`get_template_for_spec` instead.
    """
    mod_path = _REGISTRY.get(weakener_id)
    if not mod_path:
        raise TemplateNotFoundError(
            f"No prompt template registered for weakener {weakener_id!r}. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return importlib.import_module(mod_path)


def resolve_template_module_path(spec) -> str | None:
    """Return the module path for *spec*'s prompt template, or None.

    Pure mapping function (no import). Used by AdversarialSpec to compute
    ``prompt_template_id`` and ``_template_module``.
    """
    if spec.coverage_intent in ("confirm_existing", "interaction"):
        if spec.target_weakener:
            return _REGISTRY.get(spec.target_weakener)
        return None
    if spec.coverage_intent == "gap_probe":
        if not spec.source_taxonomy:
            return None
        prefix = "/".join(spec.source_taxonomy.split("/")[:2])
        return _GAP_PROBE_REGISTRY.get(prefix)
    if spec.coverage_intent == "negative_control":
        return _NEGATIVE_CONTROL_MODULE
    return None


def get_template_for_spec(spec) -> ModuleType:
    """Return the prompt-template module for *spec*, dispatching by
    ``coverage_intent``.

    Generators should prefer this over :func:`get_template` so gap_probe and
    negative_control specs are routed correctly.
    """
    mod_path = resolve_template_module_path(spec)
    if not mod_path:
        raise TemplateNotFoundError(
            f"No prompt template for spec {spec.spec_id!r} "
            f"(coverage_intent={spec.coverage_intent!r}, "
            f"target_weakener={spec.target_weakener!r}, "
            f"source_taxonomy={spec.source_taxonomy!r})"
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
