"""Skeleton-mode loader: extract identity + factor scaffold from a base COU.

v1.1 §14 Q4 resolution. Reduces COV-WRONG outcomes caused by LLM-invented
COU metadata.
"""

from __future__ import annotations

import json
import re
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
# OffsetRationale stub helpers (Phase 2.5 v0.5.11)
#
# Used by:
#   * uofa_cli.adversarial.generator._attempt_variant — runs as a post-LLM
#     mutation hook on NC packages so fresh-generated NCs include offset
#     rationale on Accepted-with-shortfall decisions
#   * tools/phase2_5/regen_nc_offset_rationale.py — re-uses the same
#     helpers for the post-hoc patch to the existing M5 corpus
#
# Phase 2.5 v0.5.12.1: moved from tools/phase2_5/ to src/uofa_cli/ so
# the installed `uofa adversarial generate` CLI can import them. The
# previous v0.5.11 location made the helpers unimportable from the
# packaged wheel (only the source-tree `python -m tools.phase2_5...`
# invocation worked), which silently broke the post-LLM hook in
# production NC generation.
#
# CE / gap_probe / interaction templates DO NOT use these helpers, so
# the W-AR-02 confirm_existing target generation continues to omit
# offset rationale (and correctly trigger the rule).
# ---------------------------------------------------------------------------

def make_offset_rationale_stub(dr_id: str, factor_id: str, factor_type: str) -> dict:
    """Return a placeholder OffsetRationale nested object (Phase 2.5 v0.5.11).

    Structurally well-formed (refersToFactor IRI + justification text), not
    substantively meaningful. Sufficient to suppress W-AR-02's noValue
    check via the `hasFactorOffset` derived-flag rule.

    The justification text is parametrized on factor_type so reviewers
    can scan the patch tool's output and see which factor each stub
    targets without dereferencing the IRI.
    """
    # Generate a deterministic-but-readable suffix from the factor_id
    factor_short = re.sub(r"[^a-z0-9-]+", "-",
                          factor_id.rsplit("/", 1)[-1].lower()).strip("-")
    return {
        "id": f"{dr_id}/offset/{factor_short}",
        "type": "OffsetRationale",
        "refersToFactor": factor_id,
        "justification": (
            f"Placeholder offset rationale (Phase 2.5 v0.5.11 corpus regen) "
            f"for {factor_type!r} factor shortfall on this Accepted decision. "
            f"The W-AR-02 rule's intent is to flag Accepted-despite-shortfall "
            f"findings that are NOT documented; structurally well-formed but "
            f"not substantively meaningful. Real-world V&V 40 cases (e.g., "
            f"Nagaraja et al. 2024 §4) record the offsetting evidence here."
        ),
    }


def _augment_dr_with_offset_rationale(doc: dict) -> tuple[dict, list[str]]:
    """Inject OffsetRationale stubs into hasDecisionRecord for every
    factor with achievedLevel < requiredLevel on an Accepted decision.

    Idempotent: skips factors that already have a referencing
    OffsetRationale on the DR.

    Returns (modified_doc, list_of_factor_ids_offset_this_run).
    """
    dr = doc.get("hasDecisionRecord")
    if not isinstance(dr, dict):
        return doc, []
    if dr.get("outcome") != "Accepted":
        return doc, []

    cf = doc.get("hasCredibilityFactor", [])
    if not isinstance(cf, list):
        cf = [cf] if cf else []

    # Collect factor IDs that need offset; synthesize an id if missing.
    shortfall_factors: list[tuple[str, str]] = []  # [(factor_id, factor_type)]
    for f in cf:
        if not isinstance(f, dict):
            continue
        req = f.get("requiredLevel")
        ach = f.get("achievedLevel")
        if req is None or ach is None:
            continue
        try:
            if ach >= req:
                continue
        except TypeError:
            continue
        ft = f.get("factorType", "Unknown")
        fid = f.get("id")
        if not fid:
            # Synthesize a deterministic IRI from the DR id + factor type
            slug = re.sub(r"[^a-z0-9-]+", "-", str(ft).lower()).strip("-")
            fid = f"{dr.get('id', '')}/factor/{slug}"
            f["id"] = fid  # mutate in place so the offset reference resolves
        shortfall_factors.append((fid, ft))

    if not shortfall_factors:
        return doc, []

    # Existing offsets (idempotency check)
    existing = dr.get("hasOffsetRationale")
    if existing is None:
        existing_list: list = []
    elif isinstance(existing, list):
        existing_list = list(existing)
    else:
        existing_list = [existing]
    already_offset = set()
    for offset in existing_list:
        if isinstance(offset, dict):
            ref = offset.get("refersToFactor")
            if ref:
                already_offset.add(ref)
        elif isinstance(offset, str):
            already_offset.add(offset)

    new_offsets: list[dict] = []
    factors_offset_this_run: list[str] = []
    for fid, ft in shortfall_factors:
        if fid in already_offset:
            continue
        stub = make_offset_rationale_stub(dr.get("id", ""), fid, ft)
        new_offsets.append(stub)
        factors_offset_this_run.append(fid)

    if new_offsets:
        # Attach as list (or extend existing list) so multiple offsets
        # can coexist if a future package needs them.
        all_offsets = existing_list + new_offsets
        # Single-element lists collapse to dict to match v0.5 conventions
        # for other 1-cardinality nested objects (hasDecisionRecord, etc.).
        dr["hasOffsetRationale"] = (
            all_offsets[0] if len(all_offsets) == 1 else all_offsets
        )

    return doc, factors_offset_this_run


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

def _make_sensitivity_analysis_stub(uofa_id: str) -> bool:
    """Return ``True`` — the ``hasSensitivityAnalysis`` value (Phase 2.5
    v0.5.15.1 schema correction).

    The v0.5 schema defines ``uofa:hasSensitivityAnalysis`` as
    ``xsd:boolean`` (per the v0.5.9 W-AL-02 schema-aligned fix and the
    JSON-LD context at ``spec/context/v0.5.jsonld``). v0.5.10/v0.5.12
    helpers incorrectly emitted it as an inline ``SensitivityAnalysis``
    object — a schema mismatch that produced SHACL violations on the
    SensitivityAnalysisShape's ``sh:datatype xsd:boolean`` constraint.
    The mismatch was masked by a separate pyshacl thread-safety bug in
    the runner's parallel SHACL validation (Phase B.9 surfaced both).

    For W-CON-04 suppression, the ``noValue(?uofa,
    uofa:hasSensitivityAnalysis)`` clause is satisfied by *any* value
    being set — boolean True is sufficient.

    The ``uofa_id`` parameter is retained for backwards compatibility
    with callers but unused.
    """
    return True


def _augment_uofa_with_sensitivity_analysis_stub(uofa: dict) -> dict:
    """Set ``hasSensitivityAnalysis: true`` on a Complete-profile UofA
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
