"""Excel import constants — generated from SHACL shapes.

DO NOT EDIT the SHACL-derived section below. Regenerate with:
    uofa schema --emit python -o src/uofa_cli/excel_constants.py

That command writes a WHOLE FILE and this one is a hybrid: the
model-credibility factor set and the base-URI constants are hand-maintained
and are not emitted here. Merge the derived section in rather than
replacing the file, or those constants are silently lost.
tests/test_excel_constants_derived.py fails if they go missing.

Source shapes:
    packs/core/shapes/uofa_shacl.ttl
    packs/vv40/shapes/vv40_shapes.ttl
    packs/nasa-7009b/shapes/nasa_7009b_shapes.ttl
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
    "Disposition",
]

# Profile name -> JSON-LD URI. Same sh:in list as VALID_PROFILES,
# so the two cannot drift apart.
PROFILE_URIS: dict[str, str] = {
    "Minimal": "https://uofa.net/vocab#ProfileMinimal",
    "Complete": "https://uofa.net/vocab#ProfileComplete",
    "Disposition": "https://uofa.net/vocab#ProfileDisposition",
}

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

# ── model-credibility (hand-maintained; mirrors packs/model-credibility/shapes/model_credibility_shapes.ttl) ──
# NIST AI RMF documentation factor set for the model-card unit. Presence-only
# (status assessed / not-assessed / scoped-out); no 1-5 levels and no risk tiers,
# per the pack spec. Grouped by the four RMF functions. NOT emitted by
# `uofa schema --emit python` (which only knows core/vv40/nasa), so keep this in
# sync with the pack shapes file by hand.
MODEL_CREDIBILITY_FACTOR_NAMES: list[str] = [
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

MODEL_CREDIBILITY_FACTOR_CATEGORIES: list[tuple[str, str]] = [
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
MODEL_CREDIBILITY_DEFAULT_OUT_OF_SCOPE: frozenset[str] = frozenset({
    "Ownership and accountability",
    "Mitigations and safeguards",
    "Residual risk",
    "Monitoring and feedback",
    "Versioning and update policy",
})

# ── NIST AI 800-3 evaluation-sufficiency factors (Group B) ──────────────────
# Hand-maintained; mirrors the AI-800-3 NodeShape in
# packs/model-credibility/shapes/model_credibility_shapes.ttl. These assess a *reported benchmark
# result* as validation evidence, the way vv40 assesses a simulation validation
# study. Presence-only like Group A: no 1-5 levels, no risk tiers.
#
# Group A (MODEL_CREDIBILITY_FACTOR_NAMES, NIST-AI-RMF-1.0) asks whether the model
# documents itself. Group B asks whether the numbers in that documentation are
# credible. They coexist in one pack and are kept mutually silent by the
# required-match factorStandard guard in each shape -- see the pack spec's
# firewall section.
AI_800_3_FACTOR_NAMES: list[str] = [
    "Score and uncertainty",
    "Item sampling",
    "Harness determinism",
    "Null calibration",
    "Context-of-use relevance",
    "Construct validity",
]

AI_800_3_FACTOR_CATEGORIES: list[tuple[str, str]] = [
    ("Score and uncertainty", "800-3 — Statistical validity"),
    ("Item sampling", "800-3 — Statistical validity"),
    ("Harness determinism", "800-3 — Reproducibility"),
    ("Null calibration", "800-3 — Reproducibility"),
    ("Context-of-use relevance", "800-3 — Decision relevance"),
    ("Construct validity", "800-3 — Decision relevance"),
]

ALL_FACTOR_CATEGORIES: list[tuple[str, str]] = (
    VV40_FACTOR_CATEGORIES
    + NASA_ONLY_FACTOR_CATEGORIES
    + MODEL_CREDIBILITY_FACTOR_CATEGORIES
    + AI_800_3_FACTOR_CATEGORIES
)

# NASA category -> assessmentPhase mapping
NASA_PHASE_MAP: dict[str, str] = {
    "NASA \u2014 Capability": "capability",
    "NASA \u2014 Results": "results",
}

# Factor standard assignment
FACTOR_STANDARD_VV40 = "ASME-VV40-2018"
FACTOR_STANDARD_NASA = "NASA-STD-7009B"
FACTOR_STANDARD_MODEL_CREDIBILITY = "NIST-AI-RMF-1.0"
FACTOR_STANDARD_AI_800_3 = "NIST-AI-800-3"

#: The column an encoder writes to say whether a required level was JUDGED.
#: **One definition, because it is a contract.** Credenza writes this header and
#: the CLI reads it; the reader locates the column BY this string rather than by
#: position, so a second copy drifting by one character would make the column
#: silently unreadable while both sides still passed their own tests. Absent on
#: older profiles, hand-built workbooks and third-party encoders -- which is why
#: the shape test survives as an advisory rather than being deleted.
LEVEL_PROVENANCE_HEADER = "Required Level Provenance"

#: Who judged the required level, and when. Beside the provenance token because
#: they are one claim: v0.8 requires a judgment token to carry its agent, and a
#: token without these is an assertion nobody stands behind.
#:
#: **The workbook gets cells rather than the shape getting an exemption.** The
#: alternative considered was letting workbook-path packages skip attribution,
#: which would fork the contract by carrier -- a JSON-LD package answering "who
#: judged this" while the same claim from a sheet shrugs. Judgment claims carry
#: their agent wherever they travel.
#:
#: A hand-edited sheet can of course assert an affirmation nobody made. That is
#: testimony, exactly like every other cell here, and the signing layer is what
#: vouches for it -- no new trust problem, and not one these columns invent.
LEVEL_AFFIRMED_BY_HEADER = "Affirmed By"
LEVEL_AFFIRMED_AT_HEADER = "Affirmed At"

#: **The workbook says what it is.** Until v0.8 the sheet carried no version
#: declaration at all, so the only way to decide whether it could speak about
#: required-level judgment was to look for the column -- inferring a contract
#: from a shape, which is the same move as inferring judgment from equal values
#: and wrong for the same reason.
#:
#: Written on `Assessment Summary` beside the other summary fields, found by
#: header like every other appended column.
WORKBOOK_PROFILE_HEADER = "Encoding Profile Version"

#: The shape an encoder writing this version produces: the anchor column, the
#: provenance token, and its two attribution cells. Bumped when the SHEET's
#: contract changes, which is not the same event as the JSON-LD context
#: changing -- they moved together at v0.8 and need not again.
WORKBOOK_PROFILE_VERSION = "v0.8"

#: The Decision sheet's anchor columns. The anchor's FORM is what tells the two
#: canonical cases apart, so it has to survive the workbook:
#:
#:   `ledger://<assessor>/<entry>`  an act of judgment -> decisionProvenance
#:                                  `asserted`; the warrant is a signature.
#:   a passage / `archive://...`    the source said it -> `extracted`; the
#:                                  warrant is this anchor, sha-pinned.
#:
#: The sha is a separate column because none of the three URI forms carries it,
#: and "the paper is their attestation" is an empty claim if a reader cannot
#: tell transcription from invention.
DECISION_ANCHOR_HEADER = "Source Anchor"
DECISION_ANCHOR_SHA_HEADER = "Anchor SHA-256"

#: A decision anchor addressing the ledger rather than a source passage.
LEDGER_ANCHOR_SCHEME = "ledger://"


#: v0.8's controlled vocabulary for `requiredLevelProvenance`. The encoding
#: tool's internal terms map INTO this set; `confirmed` deliberately has no
#: entry, because it is a location act and exporting it as a judgment claim is
#: the ambiguity v0.8 exists to kill.
LEVEL_TOKENS: dict[str, str] = {
    "extracted": "extracted",
    "defaulted": "defaulted",
    "affirmed": "affirmed",
    "corrected": "corrected",
    "waived": "waived",
    "source-absent": "source-absent",
}

#: Tokens that CLAIM a sufficiency judgment happened, and therefore must carry
#: the agent who made it.
JUDGMENT_TOKENS: frozenset = frozenset({"affirmed", "corrected", "waived"})

#: **v0.5 -> v0.8, and the jump is explained rather than discovered.** This
#: constant sat at v0.5 while the repository shipped v0.7, so every package the
#: CLI emitted declared a context two versions behind what it was written
#: against -- a declaration stating something the artifact did not do.
#:
#: The gap is NOT purely additive: v0.5 -> v0.7 removed fourteen terms
#: (`addresses`, `attestedAt`, `reviewScope`, `deploymentContext` and others).
#: The bump is safe for a specific, checked reason: **the emitter uses none of
#: the fourteen**, and packages already in the world carry their own context URL
#: which still resolves. A stale constant, not a deliberate pin.
#:
#: This moves WITH the v0.8 emission in one change. A package declaring v0.8
#: while emitting v0.7 terms would be the same stale-constant defect reborn for
#: the width of one commit.
CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.8.jsonld"
# Default namespace for identifiers minted by `uofa import`.
#
# example.org is reserved by RFC 2606 for exactly this purpose, so it is visibly
# a placeholder and prompts the author to substitute a namespace they control.
# `uofa init` already scaffolds ids under example.org; this keeps the importer
# consistent with it.
#
# This deliberately does NOT default to uofa.net. Minting there would put a
# user's private evidence under a domain they cannot serve, and because the id
# is inside the canonicalised content that the hash and signature cover, the
# mistake becomes permanent the moment the package is signed. Two organisations
# with the same project name would also mint colliding identifiers, which in RDF
# asserts that their unrelated evidence is the same thing.
#
# https://uofa.net/instances/ is reserved for this project's own published
# examples and must not be used as a default for anyone else's packages.
DEFAULT_BASE_URI = "https://example.org"

# Retained under the old name so external callers keep working.
BASE_URI = DEFAULT_BASE_URI

# Namespace reserved for the project's own shipped examples. Refused as a
# minting base so an importer run can never squat on it.
RESERVED_BASE_URIS = ("https://uofa.net", "http://uofa.net")

# ── Criteria sets ────────────────────────────────────────────
#
# A criteria set names the rubric an assessment was graded against. Published
# standards are shared concepts rather than anyone's private data, so they get a
# stable project-controlled identifier, the same reasoning that puts the
# vocabulary under uofa.net. Anything the project does not recognise is the
# author's own rubric and is minted in the author's namespace instead.
#
# Note the split is by *what the identifier names*, not by who ran the import.
# "ASME V&V 40" means the same document for everyone; "our internal rubric v3"
# does not.
CRITERIA_BASE = "https://uofa.net/criteria"

# Aliases are matched after stripping everything but letters and digits and
# upper-casing, so "ASME V&V 40", "asme-vv40-2018" and "ASME_VV40_2018" all land
# on the same canonical identifier. This is what stopped
# criteria/nasa-std-7009b and criteria/NASA-STD-7009B being two different things.
KNOWN_CRITERIA_SETS = {
    "ASMEVV402018": FACTOR_STANDARD_VV40,
    "ASMEVV40": FACTOR_STANDARD_VV40,
    "VV402018": FACTOR_STANDARD_VV40,
    "VV40": FACTOR_STANDARD_VV40,
    "NASASTD7009B": FACTOR_STANDARD_NASA,
    "NASASTD7009": FACTOR_STANDARD_NASA,
    "NASA7009B": FACTOR_STANDARD_NASA,
    "NASA7009": FACTOR_STANDARD_NASA,
    "NISTAIRMF10": FACTOR_STANDARD_MODEL_CREDIBILITY,
    "NISTAIRMF1": FACTOR_STANDARD_MODEL_CREDIBILITY,
    "NISTAIRMF": FACTOR_STANDARD_MODEL_CREDIBILITY,
}


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
