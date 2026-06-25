"""Excel import constants — generated from SHACL shapes.

DO NOT EDIT the SHACL-derived section below. Regenerate with:
    uofa schema --emit python -o src/uofa_cli/excel_constants.py

Source shapes:
    /Users/vishnu/Library/CloudStorage/Dropbox/SystemsEngineering/Praxis/uofa_github/.claude/worktrees/musing-nash/packs/core/shapes/uofa_shacl.ttl
    /Users/vishnu/Library/CloudStorage/Dropbox/SystemsEngineering/Praxis/uofa_github/.claude/worktrees/musing-nash/packs/vv40/shapes/vv40_shapes.ttl
    /Users/vishnu/Library/CloudStorage/Dropbox/SystemsEngineering/Praxis/uofa_github/.claude/worktrees/musing-nash/packs/nasa-7009b/shapes/nasa_7009b_shapes.ttl
"""

from __future__ import annotations

# ── SHACL-derived constants (do not edit) ─────────────────────

VV40_FACTOR_NAMES: list[str] = [
    "Software quality assurance",
    "Numerical code verification",
    "Discretization error",
    "Numerical solver error",
    "Use error",
    "Model form",
    "Model inputs",
    "Test samples",
    "Test conditions",
    "Equivalency of input parameters",
    "Output comparison",
    "Relevance of the quantities of interest",
    "Relevance of the validation activities to the COU",
]

NASA_ALL_FACTOR_NAMES: list[str] = [
    "Software quality assurance",
    "Numerical code verification",
    "Discretization error",
    "Numerical solver error",
    "Use error",
    "Model form",
    "Model inputs",
    "Test samples",
    "Test conditions",
    "Equivalency of input parameters",
    "Output comparison",
    "Relevance of the quantities of interest",
    "Relevance of the validation activities to the COU",
    "Data pedigree",
    "Development technical review",
    "Development process and product management",
    "Results uncertainty",
    "Results robustness",
    "Use history",
]

NASA_ONLY_FACTOR_NAMES: list[str] = [
    "Data pedigree",
    "Development technical review",
    "Development process and product management",
    "Results uncertainty",
    "Results robustness",
    "Use history",
]

VV40_LEVEL_RANGE: tuple[int, int] = (1, 5)
NASA_LEVEL_RANGE: tuple[int, int] = (0, 4)
CORE_LEVEL_RANGE: tuple[int, int] = (0, 5)
MRL_RANGE: tuple[int, int] = (1, 5)

VALID_FACTOR_STATUSES: list[str] = [
    "assessed",
    "not-assessed",
    "scoped-out",
    "not-applicable",
]

VALID_ASSESSMENT_PHASES: list[str] = [
    "capability",
    "results",
]

VALID_DECISION_OUTCOMES: list[str] = [
    "Accepted",
    "Not accepted",
]

VALID_DEVICE_CLASSES: list[str] = [
    "Class I",
    "Class II",
    "Class III",
]

VALID_ASSURANCE_LEVELS: list[str] = [
    "Low",
    "Medium",
    "High",
]

VALID_PROFILES: list[str] = [
    "Minimal",
    "Complete",
]

EVIDENCE_TYPES: list[str] = [
    "ValidationResult",
    "ReviewActivity",
    "ProcessAttestation",
    "DeploymentRecord",
    "InputPedigreeLink",
]


# ── Excel-specific constants (hand-maintained) ────────────────

SHEET_NAMES: dict[str, str] = {
    "summary": "Assessment Summary",
    "model_data": "Model & Data",
    "validation": "Validation Results",
    "factors": "Credibility Factors",
    "decision": "Decision",
}

# Row/column layout for each sheet
HEADER_ROW = 3          # Row with column headers (rows 1-2 are title + instructions)
DATA_START_ROW = 4      # First data row for Model & Data, Validation Results
FACTOR_START_ROW = 5    # First factor data row in Credibility Factors

# Factor type -> display category (for Excel template grouping)
VV40_FACTOR_CATEGORIES: list[tuple[str, str]] = [
    ("Software quality assurance", "Verification — Code"),
    ("Numerical code verification", "Verification — Code"),
    ("Discretization error", "Verification — Calculation"),
    ("Numerical solver error", "Verification — Calculation"),
    ("Use error", "Verification — Calculation"),
    ("Model form", "Validation — Model"),
    ("Model inputs", "Validation — Model"),
    ("Test samples", "Validation — Comparator"),
    ("Test conditions", "Validation — Comparator"),
    ("Equivalency of input parameters", "Validation — Assessment"),
    ("Output comparison", "Validation — Assessment"),
    ("Relevance of the quantities of interest", "Applicability"),
    ("Relevance of the validation activities to the COU", "Applicability"),
]

NASA_ONLY_FACTOR_CATEGORIES: list[tuple[str, str]] = [
    ("Data pedigree", "NASA — Capability"),
    ("Development technical review", "NASA — Capability"),
    ("Development process and product management", "NASA — Capability"),
    ("Results uncertainty", "NASA — Results"),
    ("Results robustness", "NASA — Results"),
    ("Use history", "NASA — Capability"),
]

# ── MRM-NIST (hand-maintained; mirrors packs/mrm-nist/shapes/mrm_nist_shapes.ttl) ──
# NIST AI RMF documentation factor set for the model-card unit. Presence-only
# (status assessed / not-assessed / scoped-out); no 1-5 levels and no risk tiers,
# per the pack spec. Grouped by the four RMF functions. NOT emitted by
# `uofa schema --emit python` (which only knows core/vv40/nasa), so keep this in
# sync with the pack shapes file by hand.
MRM_NIST_FACTOR_NAMES: list[str] = [
    # GOVERN — Governance & accountability
    "Ownership and accountability",
    "Intended use",
    "License and usage terms",
    "Out-of-scope use",
    # MAP — Context & risk framing
    "Task and domain context",
    "Deployment setting",
    "Known limitations",
    "Affected populations",
    # MEASURE — Evaluation & analysis
    "Evaluation metrics",
    "Evaluation methodology",
    "Bias and fairness analysis",
    "Robustness and safety testing",
    "Test and evaluation data",
    # MANAGE — Risk response & monitoring
    "Mitigations and safeguards",
    "Residual risk",
    "Monitoring and feedback",
    "Versioning and update policy",
]

MRM_NIST_FACTOR_CATEGORIES: list[tuple[str, str]] = [
    ("Ownership and accountability", "GOVERN — Governance & accountability"),
    ("Intended use", "GOVERN — Governance & accountability"),
    ("License and usage terms", "GOVERN — Governance & accountability"),
    ("Out-of-scope use", "GOVERN — Governance & accountability"),
    ("Task and domain context", "MAP — Context & risk framing"),
    ("Deployment setting", "MAP — Context & risk framing"),
    ("Known limitations", "MAP — Context & risk framing"),
    ("Affected populations", "MAP — Context & risk framing"),
    ("Evaluation metrics", "MEASURE — Evaluation & analysis"),
    ("Evaluation methodology", "MEASURE — Evaluation & analysis"),
    ("Bias and fairness analysis", "MEASURE — Evaluation & analysis"),
    ("Robustness and safety testing", "MEASURE — Evaluation & analysis"),
    ("Test and evaluation data", "MEASURE — Evaluation & analysis"),
    ("Mitigations and safeguards", "MANAGE — Risk response & monitoring"),
    ("Residual risk", "MANAGE — Risk response & monitoring"),
    ("Monitoring and feedback", "MANAGE — Risk response & monitoring"),
    ("Versioning and update policy", "MANAGE — Risk response & monitoring"),
]

# GOVERN/MANAGE subcategories that a static model card rarely documents as an
# organizational act. Marked scoped-out (out-of-scope-at-card-level) by default
# rather than not-assessed, so a genuine documentation omission is not conflated
# with an organizational artifact the card was never meant to carry. The S0
# curate step flips one to assessed when a card actually documents it (e.g. OLMo
# states a versioning/update policy). This is the v0.8 §8 open question resolved
# the honest way for the demo.
MRM_NIST_DEFAULT_OUT_OF_SCOPE: frozenset[str] = frozenset({
    "Ownership and accountability",
    "Mitigations and safeguards",
    "Residual risk",
    "Monitoring and feedback",
    "Versioning and update policy",
})

ALL_FACTOR_CATEGORIES: list[tuple[str, str]] = (
    VV40_FACTOR_CATEGORIES + NASA_ONLY_FACTOR_CATEGORIES + MRM_NIST_FACTOR_CATEGORIES
)

# NASA category -> assessmentPhase mapping
NASA_PHASE_MAP: dict[str, str] = {
    "NASA \u2014 Capability": "capability",
    "NASA \u2014 Results": "results",
}

# Profile name -> JSON-LD URI
PROFILE_URIS: dict[str, str] = {
    "Minimal": "https://uofa.net/vocab#ProfileMinimal",
    "Complete": "https://uofa.net/vocab#ProfileComplete",
}

# Factor standard assignment
FACTOR_STANDARD_VV40 = "ASME-VV40-2018"
FACTOR_STANDARD_NASA = "NASA-STD-7009B"
FACTOR_STANDARD_MRM_NIST = "NIST-AI-RMF-1.0"

CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
BASE_URI = "https://uofa.net/instances"


# ── Hand-maintained normalizers ───────────────────────────────


def normalize_evidence_type(value: str) -> tuple[str, bool]:
    """Map an evidence_type cell value to the canonical EVIDENCE_TYPES enum.

    Returns ``(normalized_value, was_substituted)``. LLM extractors sometimes
    emit descriptive domain labels (e.g. ``GridConvergenceStudy``,
    ``CodeVerification``) instead of the constrained core enum. This
    normalizer:

    1. Returns the value unchanged if already canonical.
    2. Tries a difflib fuzzy match (cutoff=0.6) — handles typos and minor
       variants like ``ValidationResults`` vs ``ValidationResult``.
    3. Falls back to ``ValidationResult`` (the most common case, and the
       reader's default for empty cells).
    """
    import difflib
    if value in EVIDENCE_TYPES:
        return value, False
    matches = difflib.get_close_matches(value, EVIDENCE_TYPES, n=1, cutoff=0.6)
    if matches:
        return matches[0], True
    return "ValidationResult", True
