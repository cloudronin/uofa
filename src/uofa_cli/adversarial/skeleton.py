"""Skeleton-mode loader: extract identity + factor scaffold from a base COU.

v1.1 §14 Q4 resolution. Reduces COV-WRONG outcomes caused by LLM-invented
COU metadata.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from uofa_cli.excel_constants import CONTEXT_URL, VV40_FACTOR_NAMES

# Top-level keys preserved verbatim into the skeleton identity block.
IDENTITY_KEYS = {
    "couName",
    "decision",
    "modelRiskLevel",
    "deviceClass",
    "assuranceLevel",
    "conformsToProfile",
    "name",
    "description",
    "id",
}

# Top-level keys re-stamped onto the generated package after the LLM returns.
PROVENANCE_KEYS = {
    "bindsRequirement",
    "bindsClaim",
    "bindsModel",
    "bindsDataset",
    "wasDerivedFrom",
    "wasAttributedTo",
    "generatedAtTime",
}

# Fields stripped from the base COU before the skeleton is used.
STRIP_KEYS = {
    "hash",
    "signature",
    "signatureAlg",
    "canonicalizationAlg",
}


class SkeletonLoadError(Exception):
    """Raised when the base COU cannot be loaded or parsed."""


# ---------------------------------------------------------------------------
# COU envelope-stub helpers (Phase 2.5 v0.5.10)
#
# Used by:
#   * tools/phase2_5/regen_nc_envelope.py — patches the M5 NC corpus to
#     suppress W-ON-02 vacuous-noValue firings on minimal NCs
#   * uofa_cli.adversarial.prompts.negative_controls._nc_render — augments
#     NC-template prompts so future NC corpus regen has the fix baked in
#
# CE / gap_probe / interaction templates DO NOT use these helpers, so the
# W-ON-02 confirm_existing target generation continues to omit envelope
# (and correctly trigger the rule).
# ---------------------------------------------------------------------------

def _make_applicability_stub(cou_id: str) -> dict:
    """Return a placeholder ApplicabilityConstraint nested object.

    Stub values per Phase 2.5 follow-up brief: structurally well-formed,
    not substantively meaningful. Sufficient to produce a triple
    `<cou> uofa:hasApplicabilityConstraint <stub-iri>` which suppresses
    W-ON-02's `noValue` check.
    """
    return {
        "id": f"{cou_id}/applicability-placeholder",
        "type": "ApplicabilityConstraint",
        "name": "Placeholder applicability constraint (v0.5.10 NC regen)",
        "description": (
            "Placeholder constraint inserted to satisfy the noValue check "
            "on uofa:hasApplicabilityConstraint in the W-ON-02 rule "
            "predicate. Not substantively meaningful."
        ),
    }


def _make_envelope_stub(cou_id: str) -> dict:
    """Return a placeholder OperatingEnvelope nested object.

    Same intent as `_make_applicability_stub`: structurally well-formed
    stub that satisfies the W-ON-02 `noValue` check on
    uofa:hasOperatingEnvelope.
    """
    return {
        "id": f"{cou_id}/envelope-placeholder",
        "type": "OperatingEnvelope",
        "name": "Placeholder operating envelope (v0.5.10 NC regen)",
        "description": (
            "Placeholder envelope inserted to satisfy the noValue check "
            "on uofa:hasOperatingEnvelope in the W-ON-02 rule predicate. "
            "Not substantively meaningful."
        ),
    }


def _augment_cou_with_envelope_stubs(cou: dict) -> dict:
    """Inject placeholder applicability + envelope into a COU dict if absent.

    Idempotent: preserves whatever's already there. Mutates the input
    dict in place AND returns it (caller can use either form).

    Used by NC prompt templates and the v0.5.10 NC corpus patch tool to
    eliminate W-ON-02 vacuous-noValue firings on minimal NC packages.
    """
    cou_id = cou.get("id", "") if isinstance(cou, dict) else ""
    if "hasApplicabilityConstraint" not in cou:
        cou["hasApplicabilityConstraint"] = _make_applicability_stub(cou_id)
    if "hasOperatingEnvelope" not in cou:
        cou["hasOperatingEnvelope"] = _make_envelope_stub(cou_id)
    return cou


# ---------------------------------------------------------------------------
# SensitivityAnalysis stub helper (Phase 2.5 v0.5.12)
#
# Used by:
#   * tools/phase2_5/regen_nc_consistency.py — patches NC corpus to
#     suppress W-CON-04 (Complete profile missing SensitivityAnalysis)
#     firings on Complete-profile NCs without an SA block
#   * uofa_cli.adversarial.prompts.negative_controls._nc_render — augments
#     NC-template prompts so future NC corpus regen has the fix baked in
#
# Note: W-CON-01 and W-AR-01 firings were addressed via PREDICATE
# tightening in the same v0.5.12 release (added factorStatus guard
# excluding 'scoped-out' and 'not-applicable' from those rules). The
# corpus-regen approach didn't apply because the firings were on
# legitimately-level-less factors, where injecting placeholder levels
# would violate the factor's stated semantics.
#
# CE / gap_probe / interaction templates DO NOT use these helpers, so
# the W-CON-04 confirm_existing target generation continues to omit
# hasSensitivityAnalysis (and correctly trigger the rule).
# ---------------------------------------------------------------------------

def _make_sensitivity_analysis_stub(uofa_id: str) -> dict:
    """Return a placeholder SensitivityAnalysis nested object.

    Stub structure: well-formed inline object with id/type/name/description.
    Sufficient to suppress the W-CON-04 noValue check on
    ``uofa:hasSensitivityAnalysis`` for Complete-profile packages without
    actual sensitivity-analysis content.
    """
    return {
        "id": f"{uofa_id}/sensitivity-analysis-placeholder",
        "type": "SensitivityAnalysis",
        "name": "Placeholder sensitivity analysis (v0.5.12 NC regen)",
        "description": (
            "Placeholder sensitivity analysis inserted to satisfy the "
            "noValue check on uofa:hasSensitivityAnalysis in the W-CON-04 "
            "rule predicate. Not substantively meaningful."
        ),
    }


def _augment_uofa_with_sensitivity_analysis_stub(uofa: dict) -> dict:
    """Inject placeholder SensitivityAnalysis into a Complete-profile UofA
    if absent.

    Idempotent: leaves an existing ``hasSensitivityAnalysis`` untouched.
    Only fires when ``conformsToProfile`` resolves to ProfileComplete
    (accepts curie ``uofa:ProfileComplete`` AND the full IRI form).
    """
    if not isinstance(uofa, dict):
        return uofa
    profile = uofa.get("conformsToProfile")
    is_complete = (
        profile == "uofa:ProfileComplete"
        or (isinstance(profile, str) and profile.endswith("ProfileComplete"))
    )
    if is_complete and "hasSensitivityAnalysis" not in uofa:
        uofa["hasSensitivityAnalysis"] = _make_sensitivity_analysis_stub(
            uofa.get("id", "")
        )
    return uofa


def load_base_cou_skeleton(base_cou: Path, pack: str = "vv40") -> dict:
    """Return a skeleton dict usable by prompt.render().

    Keys: identity (dict), factor_scaffold (list of stubs), decision_shell
    (hasDecisionRecord object), context_of_use (inline object), top_level_stamps
    (dict of PROVENANCE_KEYS), context_url (string).

    Raises SkeletonLoadError on parse failure or missing identity fields.
    """
    path = _resolve_base_cou_path(base_cou)
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise SkeletonLoadError(f"failed to read base COU {path}: {e}") from e

    if not isinstance(doc, dict):
        raise SkeletonLoadError(f"base COU is not a JSON-LD object: {path}")

    identity = {k: doc[k] for k in IDENTITY_KEYS if k in doc}
    if not identity.get("name"):
        raise SkeletonLoadError(f"base COU missing required 'name' field: {path}")

    context_of_use = deepcopy(doc.get("hasContextOfUse"))
    decision_shell = deepcopy(doc.get("hasDecisionRecord"))

    factor_scaffold = _build_factor_scaffold(doc, pack)

    top_level_stamps = {k: deepcopy(doc[k]) for k in PROVENANCE_KEYS if k in doc}

    return {
        "identity": identity,
        "context_of_use": context_of_use,
        "decision_shell": decision_shell,
        "factor_scaffold": factor_scaffold,
        "top_level_stamps": top_level_stamps,
        "context_url": CONTEXT_URL,
        "source_path": str(path),
    }


def _resolve_base_cou_path(base_cou: Path) -> Path:
    p = Path(base_cou)
    if p.is_dir():
        candidates = sorted(p.glob("uofa-*.jsonld")) or sorted(p.glob("*.jsonld"))
        if not candidates:
            raise SkeletonLoadError(f"no *.jsonld file found in base COU dir: {p}")
        return candidates[0]
    if not p.exists():
        raise SkeletonLoadError(f"base COU file not found: {p}")
    return p


def _build_factor_scaffold(doc: dict, pack: str) -> list[dict]:
    """Return a list of factor stubs with factorType pre-populated.

    Uses the factor types already in the base COU if present; otherwise falls
    back to the canonical list for the pack. ``factorStandard`` is preserved.
    """
    existing = doc.get("hasCredibilityFactor", []) or []
    standard = _infer_factor_standard(existing, pack)
    if existing:
        scaffold: list[dict] = []
        for f in existing:
            if not isinstance(f, dict):
                continue
            ft = f.get("factorType")
            if not ft:
                continue
            scaffold.append({
                "type": "CredibilityFactor",
                "factorType": ft,
                "factorStandard": f.get("factorStandard", standard),
            })
        if scaffold:
            return scaffold

    # Fallback: canonical VV40 factor list.
    return [
        {"type": "CredibilityFactor", "factorType": name, "factorStandard": standard}
        for name in VV40_FACTOR_NAMES
    ]


def _infer_factor_standard(existing: list, pack: str) -> str:
    for f in existing or []:
        if isinstance(f, dict) and f.get("factorStandard"):
            return f["factorStandard"]
    if pack == "vv40":
        return "ASME-VV40-2018"
    if pack in {"nasa-7009b", "nasa"}:
        return "NASA-STD-7009B"
    return "ASME-VV40-2018"
