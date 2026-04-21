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

ALL_FACTOR_CATEGORIES: list[tuple[str, str]] = VV40_FACTOR_CATEGORIES + NASA_ONLY_FACTOR_CATEGORIES

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

CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
BASE_URI = "https://uofa.net/instances"
