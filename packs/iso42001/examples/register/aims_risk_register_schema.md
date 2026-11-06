# AIMS Risk Register: structure, UofA extensions, and pack gap

Extracted 2026-11-01 from one real ISO 42001 AI risk assessment workbook (19 rows, v1.0, printed to PDF).
Organizational content is excluded. Only the shape is recorded here. The synthetic fixture
`acme-register.xlsx` is built from this schema.

## 1. Workbook tabs, in the order the workbook says to fill them

| # | Tab | Purpose | Filled by |
|---|---|---|---|
| 1 | Document Control | Document name, owner, type, approver, issuer, preparer, effective date, last reviewed, next review; version table (date, name, version, description of changes) | Document owner |
| 2 | Introduction | Purpose, scope (five asset classes: information, digital, physical, site, people), approach, how-to-use text | Document owner |
| 3 | Impact Evaluation | 1 to 5 scale with label, definition, and monetary loss band | Fixed |
| 4 | Probability Evaluation | 1 to 5 scale with label and probability band | Fixed |
| 5 | Time Horizon | Short 0 to 3 months, medium 3 to 12, long over 12; priority matrix of risk level by horizon (1 highest, 9 lowest) | Fixed |
| 6 | Control Evaluation | 1 to 5 scale: Effective, Limited improvement needed, Moderate improvement needed, Significant improvement needed, Ineffective, each with a description | Fixed |
| 7 | Risk Levels | Risk = Probability x Impact, 5x5 grid 1 to 25, banded Low / Medium / High | Fixed |
| 8 | AI Risk Assessment | The master register, one row per risk | Assessor, SMEs, risk owners |

The register also references two external artifacts that are not in the workbook: a per-risk
"Risk Treatment Plans" workbook (one tab per treated risk) and a "Comprehensive Risk Treatment Plan"
page in a wiki tool. Those are where completion evidence would live, if it exists.

## 2. The scales

Impact (1 to 5): Insignificant, Minor, Moderate, Major, Business Critical. Loss bands observed:
under 200k, 200k to 1M, 1M to 5M, 5M to 25M, 25M and up (currency euro in the source).

Probability (1 to 5): Remote 1 to 19 percent, Unlikely 20 to 39, Likely 40 to 59, Highly Likely 60 to 79,
Near Certainty 80 to 99.

Control effectiveness (1 to 5): 1 Effective, 2 Limited improvement needed, 3 Moderate improvement needed,
4 Significant improvement needed, 5 Ineffective.

Risk level bands, inferred from the 19 rows (the grid colors did not survive PDF extraction):
score 1 to 6 Low, 7 to 14 Medium, 15 to 25 High. Observed: 6 Low, 8 Medium, 12 Medium, 15 High, 20 High.

Risk acceptance criteria, inferred: Low and Medium residuals were accepted (every row answered Yes,
including Medium 10). The criteria text itself is not in the workbook. Treat as an open field.

## 3. The master register row

Four column groups, left to right. Types as observed.

### 3.1 Risk evaluation (inherent)

| Column | Type | Notes |
|---|---|---|
| Risk # | id, `QAIR-NNN` pattern | sequential |
| Risk Name | short text | e.g. Data Poisoning, Prompt Injection, Fairness and Bias |
| Description | one sentence | |
| Impact | int 1 to 5 | |
| Probability | int 1 to 5 | inherent |
| Time Horizon | int | observed 2, 3, 4; the Time Horizon tab defines only three bands, the column's encoding is not stated in the workbook. Investigation item. |
| Risk Evaluation Calculation | formula | Impact x Probability |
| Inherent Risk | enum | Low Risk / Medium Risk / High Risk, from the band |
| Risk Treatment Options | enum | Mitigate / Accept (Avoid, Transfer presumably allowed, not observed) |
| Control Framework Mapping | list of control ids | NIST 800-53 style ids (AC-2, RA-5, SR-9, CM-3, AT-3, CP-2, CM-2(2)) plus a custom AI-N family (AI-4, AI-5(1), AI-8, AI-10, AI-14, AI-15). One to seven per row |

### 3.2 Risk and control analysis

| Column | Type | Notes |
|---|---|---|
| Expected Controls / Actions | bulleted prose | generic good-practice list per risk, reads like a framework excerpt |
| Existing Controls | prose with `Label:` then `Control:` sub-blocks | the organization's actual claim. Observed sub-labels: Code, Model, Transformation, Access, Verification, Dependencies, Deployment Tool, Data Acquisition, Ingestion, Storage, Preparation. Several blocks repeat verbatim across rows. Some blocks state a gap in plain words ("no automated verification", "dependent on individual project leads", "on a use-case-by-use-case basis"). None cites a file, record, or run. |

### 3.3 Risk treatment (current state)

| Column | Type | Notes |
|---|---|---|
| Control Effectiveness | enum 1 to 5 label | self-assessed |
| Current Probability | int 1 to 5 | after existing controls |
| Risk Treatment Calculation | formula | Impact x Current Probability |
| Residual Risk | enum | band of the above |
| Risk Treatment Options | enum | Mitigate / Accept; "N/A, residual risk is low" used as a value when Accept |
| Risk Treatment Plan | prose | one to three actions, often with a person's name inline and a pointer to the external treatment-plan tab or wiki page |
| Risk Treatment Estimate Completion | date | observed range 2025-06 to 2026-03 |
| Probability After Treatment | int 1 to 5 | assumed, not evidenced |

### 3.4 Residual risk acceptance

| Column | Type | Notes |
|---|---|---|
| Residual Risk Calculation | formula | Impact x Probability After Treatment |
| Residual Risk After Treatment | enum | band |
| Within Risk Acceptance Criteria | Yes / No | |
| Risk Owner | person | the acceptor. In the source, one person on 14 of 19 rows, and that person also owns most of the controls |

### 3.5 What the row does not carry

No column for: evidence reference behind an Existing Control; whether a control is mandated or
discretionary; treatment completion date; completion evidence; who owns the control as distinct from
who accepts the residual; when the row was last reviewed. Every "after treatment" number therefore rests
on an assumption the register cannot check.

## 4. UofA onboarding template: the columns the tool adds

These are the columns `uofa extract <bundle>` must populate from the raw evidence folder and
`uofa import` must carry into the package. Each added cell follows the existing extract conventions
(confidence color, source comment naming the file and page).

| Added column | Source in bundle | Feeds |
|---|---|---|
| Existing Control Evidence Ref | path plus hash of the record that shows the control operating (CI log, MRM card, review record, access list export) | `ControlImplementationRecord` with evidence pointer; W-AIMS-CONTROL-UNEVIDENCED when empty |
| Control Type | Mandated / Discretionary, extracted from the control text ("required for all" vs "when needed", "at the discretion of") | W-AIMS-CONTROL-DISCRETIONARY |
| Self-Declared Gap | Yes / No, extracted from the control text ("no automated", "not currently", "relies solely on") | W-AIMS-EFFECTIVENESS-CONTRADICTED when Yes and effectiveness is 1 or 2 |
| Control Owner | person or role | independence check |
| Treatment Completed Date | date or blank | W-AIMS-TREATMENT-OVERDUE |
| Treatment Completion Evidence Ref | path plus hash | same |
| Acceptor | person who signed residual acceptance | W-AIMS-ACCEPTOR-NOT-INDEPENDENT when equal to Control Owner |
| Row Last Reviewed | date | W-AIMS-REGISTER-STALE (with Document Control next-review date) |

Derived in-sheet, also derived in the pack: Days Overdue (due date past, no completion),
Residual Earned (Yes only when completion evidence exists or treatment was Accept).

## 5. What the iso42001 pack (v0.5.0) already does, and the gap

Checked against `packs/iso42001` at github.com/cloudronin/uofa, main, 2026-11-01.

### Already there

| Asset | Where | State |
|---|---|---|
| Classes `RiskRegister`, `RiskEntry`, `RiskTreatmentPlan`, `RiskAcceptanceRationale`, `ControlEffectivenessAssessment`, `ControlImplementationRecord` | `shapes/iso42001_shapes.ttl` | defined |
| Properties `treatmentDecision`, `riskLikelihood`, `riskSeverity`, `riskOwner`, `riskCategory`, `mappedToControl`, `hasRiskTreatmentPlan`, `hasAcceptanceRationale` | same | defined |
| Shapes: every `RiskEntry` maps to a control; Mitigate needs a plan; Accept needs a rationale | `SoARiskMappingShape`, `SoARiskTreatmentShape` | defined, never exercised |
| `AIMSControl` design and operational effectiveness fields, 1 to 3 or "Not yet assessed" | `SoAControlDEOEShape` | defined |
| W-AR-02: Accept rationale present but empty | `rules/iso42001_weakener.rules` line 83 | the only rule that touches `RiskEntry` |
| OOS rule: risk identification completeness needs a methodology and an external-framework comparison | `rules/oos/oos_v0.1.rules` rule 2 | fires at package level |
| OOS rule: control operational effectiveness needs independent verification | rule 3 | fires per claim, not per register row |
| Excel round trip: `uofa extract folder -> xlsx`, `uofa import xlsx -> jsonld` | `src/uofa_cli/commands/extract_cmd.py`, `import_excel.py`, `excel_writer.py`, `excel_mapper.py` | works, but the template is factor-shaped (V&V 40 and NASA sheets: Assessment Summary, Model & Data, Validation Results, Credibility Factors, Decision) |

### Not there

| Gap | Evidence |
|---|---|
| No `RiskEntry` instance exists in any example or calibration package. The register is one node with a prose description ("12-entry register: ...") | `grep -c RiskEntry` returns 0 across `examples/hybrid/*` and `specs/calibration/packages/cal-aims-*` |
| No properties for inherent score, current probability, residual score, per-row control effectiveness rating, treatment due date, treatment completion, probability after treatment, acceptance criteria, acceptor | shapes file |
| No weakener for: treatment past due without completion; control claimed without evidence pointer; discretionary practice recorded as control; effectiveness rating contradicting the control text; acceptor equals control owner; register past its review date (W-AIMS-AUDIT-STALE covers internal audits only) | rules file, 15 patterns |
| No iso42001 Excel template. `excel_constants.py` is generated from core, vv40, and nasa-7009b shapes only | file header |
| `extract` has no register-row entity type; its entities are model, data, validation result, factor, decision | `excel_writer.py` sheet list |

### Build list, dependency order

1. Vocabulary: add the row-level properties above to `iso42001_shapes.ttl`; add `RiskEntryShape` requiring id, name, impact, inherent probability, treatment decision, risk owner.
2. Fixture: encode `acme-register.xlsx` as JSON-LD by hand once, with one `RiskEntry` per row. This is the first package in the repo with real register rows.
3. Rules: the six W-AIMS patterns in section 4. Overdue and stale need date arithmetic, so they go through the SPARQL derivation pre-pass like the existing v0.5 rules. Discretionary and self-declared gap need an extraction flag, so they consume a column, not raw prose.
4. Template: an iso42001 branch in `excel_writer._create_blank_sheets` producing the eight tabs in section 1 plus the section 4 columns; `excel_mapper` branch producing `RiskEntry` nodes; regenerate `excel_constants.py`.
5. Extract: a register-row entity type for the LLM extractor, with the two text-classification fields (control type, self-declared gap) as enumerated outputs.
6. Report: a "register verification" section in `uofa report` ordered as: residuals resting on unevidenced treatment, controls with no evidence ref, rating contradictions, independence.

Steps 1 to 3 run in parallel now. Step 4 consumes 1. Step 5 consumes 4. Step 6 consumes 3.

## 6. Investigation items before any of this is asserted in a spec

- Confirm against the ISO/IEC 42001:2023 text that clauses 6.1.2, 6.1.3, 8.2, 8.3, and 9.1 are the right anchors for the register columns. Believed correct, not verified from the text in this session.
- Confirm the major / minor / OFI grading rule the certification body applies (ISO/IEC 17021-1 plus ISO/IEC 42006).
- Resolve the Time Horizon column encoding (section 3.1).
- Confirm the source workbook's Low / Medium / High band edges from the Risk Levels tab colors; the bands here are inferred from 19 data points.
