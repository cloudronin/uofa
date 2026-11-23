# UofA iso42001 Pack Spec v0.6: Register-based readiness engagement

Status: draft for build. Author: Vishnu Vettrivel. Date: 2026-11-01.
Supersedes nothing; extends pack v0.5.0 (derivation pre-pass). Companion files under `packs/iso42001/examples/register/`:
`aims_risk_register_schema.md`, `acme-register.xlsx`, `build_synthetic_register.py`.

## 0. The one-sentence goal

A reviewer takes a customer's existing AIMS documents as a folder, runs `uofa extract`, reviews and
dispositions the resulting register workbook, runs `uofa import`, runs `uofa check`, and hands the customer
a readiness report whose first page says which residual risks rest on work they cannot show they finished.

## 1. The engagement pipeline

| Step | Command | Input | Output | Exists today |
|---|---|---|---|---|
| 1 | `uofa evidence seal <bundle>/` | customer folder | sealed manifest sidecar: path, sha256, size per file | yes (`import --evidence` consumes it). Investigation item I1: confirm it accepts an arbitrary folder, not only solver outputs |
| 2 | `uofa extract <bundle>/ --pack iso42001 -o register.xlsx` | folder plus sidecar | register workbook, green cells filled, each with confidence color and source comment | no. Refused today: manifest names no prompt or template |
| 3 | reviewer edits `register.xlsx` | workbook | dispositioned workbook: every row Confirm / Correct / Blank / Added, Reviewed By, Reviewed At | partly. Attribution columns exist for factor sheets, not for a register |
| 4 | `uofa import register.xlsx --pack iso42001 --evidence <sidecar> --sign` | workbook | signed JSON-LD with one `RiskEntry` per row | no register mapping |
| 5 | `uofa check --pack iso42001 package.jsonld` | package | SHACL plus C3 firings plus OOS gaps | engine yes; register rules no |
| 6 | `uofa report package.jsonld --pack iso42001 --format html` | package | readiness report | report exists, factor-shaped; needs a register section |

Steps 1 and 5 and 6 are engine work that exists. The build is steps 2, 3, 4 and the rules behind 5.

## 2. Scope

In scope: the AI risk register (clauses 6.1.2, 6.1.3, 8.2, 8.3) and the document-control header. The register
is where a 42001 Stage 2 auditor spends sampling time, and it is the one artifact every customer already has.

Out of scope for v0.6: Statement of Applicability import (shape exists, no template), impact assessments,
internal audit records, management review. Those are v0.7 and reuse the same template mechanism.

Investigation item I2: confirm against the ISO/IEC 42001:2023 text that 6.1.2, 6.1.3, 8.2, 8.3, 9.1 are the
clause anchors for the register columns. Believed correct. Not verified from the text.

## 3. Vocabulary and shapes (`packs/iso42001/shapes/iso42001_shapes.ttl`)

### 3.1 New properties on `uofa-aims:RiskEntry`

| Property | Range | Workbook column |
|---|---|---|
| `riskId` | string, `^[A-Z]{2,5}-\d{3}$` | Risk # |
| `riskName` | string | Risk Name |
| `riskDescription` | string | Description |
| `inherentImpact` | integer 1 to 5 | Impact |
| `inherentProbability` | integer 1 to 5 | Inherent Probability |
| `timeHorizon` | integer 1 to 3 | Time Horizon (I3: encoding in real workbooks varies; import normalizes, records the raw value in `fieldProvenance`) |
| `inherentScore`, `inherentBand` | integer; enum Low / Medium / High | computed on import, not read from the sheet |
| `controlFrameworkRef` | list of strings | Control Framework Mapping |
| `expectedControlsText` | string | Expected Controls / Actions |
| `hasExistingControl` | `ControlImplementationRecord`, one per `Label:` block in the Existing Controls cell | Existing Controls |
| `controlEffectivenessRating` | integer 1 to 5 | Control Effectiveness |
| `currentProbability` | integer 1 to 5 | Current Probability |
| `currentScore`, `currentBand` | computed | |
| `treatmentDecision` (exists) | Mitigate / Accept / Avoid / Transfer | Treatment Option (current) |
| `hasRiskTreatmentPlan` (exists) | `RiskTreatmentPlan` | Risk Treatment Plan |
| `probabilityAfterTreatment` | integer 1 to 5 | Probability After Treatment |
| `residualScore`, `residualBand` | computed | |
| `withinAcceptanceCriteria` | boolean | Within Acceptance Criteria |
| `riskOwner` (exists) | IRI of a `RoleAssignment` or person node | Risk Owner (acceptor) |
| `controlOwner` | IRI | Control Owner |
| `rowLastReviewed` | dateTime | Row Last Reviewed |

### 3.2 New properties on `uofa-aims:ControlImplementationRecord`

| Property | Range | Column |
|---|---|---|
| `controlLabel` | string | the `Label:` before the colon |
| `controlText` | string | the `Control:` body |
| `evidenceRef` | IRI, `archive://<sealed path>#sha256:<hash>` form, zero or more | Existing Control Evidence Ref |
| `controlType` | Mandated / Discretionary | Control Type |
| `selfDeclaredGap` | boolean | Self-Declared Gap |

### 3.3 New properties on `uofa-aims:RiskTreatmentPlan`

| Property | Range | Column |
|---|---|---|
| `treatmentText` | string | Risk Treatment Plan |
| `dueDate` | dateTime | Treatment Estimated Completion |
| `completedDate` | dateTime, optional | Treatment Completed Date |
| `completionEvidenceRef` | IRI, optional | Treatment Completion Evidence Ref |

### 3.4 New class `uofa-aims:RegisterDocumentControl`

Properties: `documentName`, `documentOwner`, `approvedBy`, `effectiveDate`, `lastReviewedDate`,
`nextReviewDate`, `version`. One per package. Hangs off `RiskRegister` via `hasDocumentControl`.

### 3.5 Shapes

| Shape | Rule |
|---|---|
| `RiskEntryShape` | required: riskId, riskName, inherentImpact, inherentProbability, treatmentDecision, riskOwner. Integer ranges enforced. |
| `SoARiskTreatmentShape` (exists) | unchanged: Mitigate needs a plan, Accept needs a rationale |
| `SoARiskMappingShape` (exists) | relax to `sh:severity sh:Warning` for v0.6. Real registers map to framework ids, not to Annex A controls; a hard failure here would reject every real customer register. I4: decide whether `controlFrameworkRef` satisfies it via a crosswalk, or whether the SoA import in v0.7 is where this bites. |
| `RiskTreatmentPlanShape` | required: dueDate when the parent row is Mitigate |
| `RegisterDocumentControlShape` | required: nextReviewDate, documentOwner |

Design note: `inherentScore` and bands are computed on import from the two integers, never read from the
sheet. A sheet whose formula cell disagrees with the integers is a finding (section 5, W-AIMS-SCORE-MISMATCH),
not an input.

## 4. The workbook template (`packs/iso42001/templates/iso42001-register-template.xlsx`)

Built from `build_synthetic_register.py` with the data rows removed and one example row kept, per the
workbook convention. Tabs and columns exactly as in `aims_risk_register_schema.md` sections 1, 3 and 4, plus
the disposition block.

### 4.1 Disposition block (added columns AJ to AM on AI Risk Assessment)

| Column | Values | Who writes |
|---|---|---|
| Disposition | Confirm / Correct / Blank / Added | reviewer, one per row. Same four verbs as the Johnson pilot and Encoding Protocol v0.2 |
| Reviewer Note | free text | reviewer |
| Reviewed By | `ledger://<reviewer>/<entry>` | reviewer |
| Reviewed At | dateTime | reviewer |

Rules: `extract` writes rows with Disposition blank. `import --protocol-check` refuses a workbook with any
blank Disposition. `Correct` requires the corrected cell to differ from the extract value, which import
recovers from the cell's source comment and records in `fieldProvenance` as `extracted-then-corrected`.
`Added` rows carry no extract comment and are recorded `asserted`. This is the existing asserted-versus-
extracted split from the Decision sheet applied row-wide.

### 4.2 Evidence reference cells

Form: `archive://<path relative to bundle root>#sha256:<hex>`. `import --evidence <sidecar>` checks every
`evidenceRef` and `completionEvidenceRef` against the sidecar; a reference whose path or hash is not in the
seal is refused by name. A customer cannot cite a file they did not hand over.

### 4.3 Assessment Summary additions

`Encoding Profile Version` cell declares `v0.10` (I5: confirm the bump is warranted under the rule in
`excel_constants.py`, which says bump when the sheet's contract changes; it does). `Register Checks` tab is
kept as a reviewer convenience; import ignores it.

## 5. Weakener catalog additions (`packs/iso42001/rules/iso42001_weakener.rules` plus derivations)

Seven C3 patterns. Severity on the existing High / Medium / Low scale. Each lists the fixture rows that
must fire it and the rows that must not (over-firing discipline, same as cal-aims).

| Pattern id | Fires when | Severity | Needs derivation | Fixture rows fire | Must stay silent |
|---|---|---|---|---|---|
| W-AIMS-TREATMENT-OVERDUE | Mitigate row; plan dueDate before `assessmentDate`; no completedDate | High | yes, date compare | 002, 005, 007, 008, 012 | 003, 006, 010 |
| W-AIMS-RESIDUAL-UNEARNED | Mitigate row; residualBand claimed; no completionEvidenceRef | High | no | the five above plus 011 | 003, 006, 010 |
| W-AIMS-CONTROL-UNEVIDENCED | a ControlImplementationRecord with controlText and zero evidenceRef | Medium | no | 005, 011 | all others |
| W-AIMS-CONTROL-DISCRETIONARY | controlType Discretionary on a row whose treatmentDecision is Accept or whose currentBand is Low | Medium | no | 008, 012 | all others |
| W-AIMS-EFFECTIVENESS-CONTRADICTED | controlEffectivenessRating 1 or 2 and any ControlImplementationRecord with selfDeclaredGap true | High | no | 001, 003 | all others |
| W-AIMS-ACCEPTOR-NOT-INDEPENDENT | riskOwner IRI equals controlOwner IRI | Medium | yes, IRI equality across nodes | 001, 002, 007, 009, 011 | 003, 004, 005, 006, 008, 010, 012, 013 |
| W-AIMS-REGISTER-STALE | RegisterDocumentControl nextReviewDate before `assessmentDate` | Medium | yes, date compare | whole register | n/a |
| W-AIMS-SCORE-MISMATCH | a sheet score cell disagrees with impact times probability | Low | no | none in fixture; add one row in the test package | all |

`assessmentDate` is a package-level literal set by `import` from the Register Checks cell B2, defaulting to
the import timestamp. It is recorded in `fieldProvenance` so the reader can see which date "overdue" was
judged against.

Boundary with OOS: the existing OOS rule `oos_aims_control_operational_effectiveness_warranted` keeps its
job. An evidence pointer satisfies CONTROL-UNEVIDENCED (the record exists); it does not satisfy the OOS
rule (nobody independent checked it). The report shows both, labeled differently.

The existing `W-AR-02` (Accept with empty rationale) stays. The template's "N/A, residual risk is low" string
in the plan cell is mapped on import to a `RiskAcceptanceRationale` whose justification is that string, so
W-AR-02 does not fire on it; the reviewer can mark it `Correct` if the real rationale is thinner than that.

## 6. Extraction (`packs/iso42001/prompts/iso42001_register_extract_prompt.txt`, `llm_extractor.py`)

### 6.1 Code changes

| Where | Change |
|---|---|
| `packs/iso42001/pack.json` | add `"prompt"` and `"template"` keys. This alone lifts the refusal in `_extract_refusal`. |
| `llm_extractor.ExtractionResult` | add `document_control: dict[str, FieldExtraction]` and `risk_register: list[dict[str, FieldExtraction]]` |
| `llm_extractor._json_to_result` | parse the two new blocks when `pack_name == "iso42001"` |
| `excel_writer.write_extraction` | branch: when the template has an `AI Risk Assessment` sheet, write `risk_register` rows there and `document_control` to Document Control. Existing confidence color and source comment helpers reused as-is. |
| `excel_writer._create_blank_sheets` | iso42001 branch producing the eight tabs (only reached when the template file is missing; keep it for parity) |

### 6.2 What the prompt asks for

Per row: every column in schema section 3 (the customer's own values, verbatim), plus the three
classification fields from section 4 of the schema, each with a one-line quote justifying it:

- `control_type`: Discretionary when the control text says it runs case-by-case, when needed, when an obvious
  need is identified, or depends on a named individual's judgment. Otherwise Mandated.
- `self_declared_gap`: true when the control text states an absence: no automated, not currently, relies
  solely on, dependent on individual.
- `evidence_ref`: the sealed bundle path of a document that shows the control operating, only if such a
  document is in the corpus. Never invented. Empty is the correct answer when nothing in the folder backs
  the claim; that empty cell is the finding.

Document control: name, owner, approver, effective, last reviewed, next review, version.

Corpus: the folder, chunked per the existing `_chunked_extraction`. Registers arrive as xlsx or as PDF
prints of xlsx; `readers/xlsx_reader.py` and `document_reader.py` exist. I6: confirm `document_reader` keeps
cell-to-column adjacency on a PDF-printed spreadsheet, because the source workbook's PDF scattered column
groups across pages. If it does not, the register tab is read through `xlsx_reader` when the customer can
supply the xlsx, and the PDF path is a documented degradation.

### 6.3 Keyless path

Not supported for iso42001 in v0.6. `KEYLESS_PACKS` unchanged. The refusal message already says so.

## 7. Import (`excel_mapper.py`, `excel_reader.py`, `excel_constants.py`)

| Change | Detail |
|---|---|
| `excel_reader` | read the eight tabs by header name, not position, following the existing `_find_data_row` and header-lookup convention |
| `excel_mapper.map_workbook` | iso42001 branch: one `RiskEntry` per row; one `ControlImplementationRecord` per `Label:` block split on the `Label:\nControl:` pattern; one `RiskTreatmentPlan` or `RiskAcceptanceRationale` per row by treatmentDecision; one `RegisterDocumentControl`; person strings minted as `RoleAssignment` nodes under `--base-uri`, deduplicated by exact string so the independence rule can compare IRIs |
| computed fields | inherentScore, currentScore, residualScore and bands computed here; sheet formula cells read only to populate W-AIMS-SCORE-MISMATCH |
| `fieldProvenance` | every register cell: `extracted`, `extracted-then-corrected`, or `asserted`, from the disposition block |
| `derive_profile` | unchanged; the new shapes feed it through `_profile_requirements` |
| `excel_constants.py` | regenerate the derived section with `uofa schema --emit python`; add `ISO42001_SHEET_NAMES`, `REGISTER_HEADER_ROW = 2`, `REGISTER_DATA_START_ROW = 3`, the disposition header strings |
| `--protocol-check` | add the register workbook-side checks: no blank Disposition, every evidenceRef resolves in the sidecar, Encoding Profile Version is v0.10 |

## 8. Report (`commands/report.py`, `report_state.py`, `weakener_focus.py`)

The report is the engagement deliverable. New section "Register readiness", rendered first when the package
holds a `RiskRegister`, in this order:

1. Headline table: rows whose residual rests on an overdue or unevidenced treatment. Columns: risk id, name,
   claimed residual band, due date, days overdue, what would close it (the plan text, verbatim).
2. Controls with no evidence reference, grouped by row.
3. Rating contradictions: the rating, and the sentence in the control text that contradicts it, quoted.
4. Discretionary controls.
5. Independence: rows where the acceptor owns the control.
6. Register staleness and document-control header.
7. OOS evidence requests (existing rendering), labeled "documentation to request from the organization".

Each finding line names the pattern id, the row, and the cell. No remediation advice beyond quoting the
customer's own plan text; that is the existing Copilot boundary.

I7: `weakener_focus.enrich_firings` attaches a factor focus per pack manifest. Register firings focus on a
`RiskEntry`, not a factor. Confirm whether the focus map accepts an arbitrary `affectedNode` class or needs a
second map keyed by row. Grep before building; this is the one place the report may need a real change
rather than a section.

Register language: "readiness" and "gaps". Never "certifiable", "audit-ready", "will pass". The report states
what the register shows and does not show.

## 9. Fixtures and tests

| Fixture | Source | Purpose |
|---|---|---|
| `packs/iso42001/examples/register/acme-register.xlsx` | `build_synthetic_register.py` | round-trip input |
| `packs/iso42001/examples/register/acme-register.jsonld` | hand-encoded once from the xlsx in step B, then regenerated by import in step D and diffed | the first package in the repo with real `RiskEntry` rows; rule oracle |
| `packs/iso42001/examples/register/acme-bundle/` | eight to ten short synthetic documents generated from the row data: AI policy, the register as xlsx and as PDF print, a CI log, a model risk card, a training roster export, a bucket lifecycle policy, a branch-protection export, a failover drill note. Names match the evidence refs in the xlsx. | extract input; sealed by step 1 |
| `tests/test_iso42001_register.py` | new | see gates |

The Seeded Defects tab in the synthetic workbook is the test oracle. Each pattern's test asserts the fire set
and the silent set from section 5 exactly.

## 10. Build plan

Paired Claude Code sessions. Hours are paired hours. Dependency order only; everything marked parallel-now
can start today.

| Phase | Work | Hours | Depends on | Done-gate |
|---|---|---|---|---|
| A | Vocabulary, shapes, pack.json keys (section 3) | 3 | none, parallel-now | `uofa shacl` passes on a hand-written three-row package; `packs iso42001 --detail` lists the new shapes |
| B | Hand-encode `acme-register.jsonld` from the synthetic xlsx; synthetic bundle folder (section 9) | 4 | none, parallel-now | package validates under A's shapes; bundle seals under step 1 |
| C | Seven rules plus derivations (section 5) | 5 | A, B | G1: on `acme-register.jsonld`, every pattern fires exactly its row set, clean rows 004, 006, 010, 013 fire nothing; existing 77 pack tests still pass |
| D | Template, reader, mapper, constants, protocol-check (sections 4, 7) | 6 | A | G2: `uofa import acme-register.xlsx` produces a package whose `check` output equals G1's firing set; diff against the hand-encoded package shows only IRIs and timestamps |
| E | Extract prompt, result fields, writer branch (section 6) | 6 | B, D | G3: `uofa extract acme-bundle/` fills at least 10 of 13 evidence refs correctly, classifies control type on 13 of 13, self-declared gap on 13 of 13, invents zero refs; blank Disposition on every row |
| F | Report section (section 8) | 4 | C | G4: a reader who has not seen the fixture names the five overdue rows from the report alone, in under five minutes |
| G | Engagement runbook: the six commands, folder layout the customer is asked for, what the reviewer does at step 3, the report hand-off | 2 | E, F | runbook executed end to end on the synthetic bundle by following only the runbook text |

Total about 30 paired hours. A, B parallel-now. C and D parallel after A. E after D. F after C. G last.

## 11. Acceptance for the engagement, not the code

The build is done when one stranger's register (the design partner's) goes through steps 1 to 6 and the
customer confirms, in writing, that the headline table matched what they knew and surfaced at least one
thing they did not. That is the done-test. It is not a code gate and it cannot be closed from inside the
repo.

## 12. Investigation items, consolidated

| Id | Question | Who confirms | Blocks |
|---|---|---|---|
| I1 | Does `uofa evidence seal` accept an arbitrary document folder | execution agent, grep `commands/evidence.py` | B |
| I2 | Clause anchors 6.1.2, 6.1.3, 8.2, 8.3, 9.1 against the standard text | Vishnu, standard in hand | report wording only |
| I3 | Time Horizon encoding in real workbooks | first design-partner register | nothing; import normalizes and records raw |
| I4 | Whether `controlFrameworkRef` can satisfy `SoARiskMappingShape` through a crosswalk, or SoA import in v0.7 is where it bites | execution agent | D (severity decision only) |
| I5 | Encoding Profile Version bump to v0.10 and Credenza pin | execution agent, grep Credenza pin | D |
| I6 | PDF-printed spreadsheet column adjacency in `document_reader` | execution agent, test on the synthetic PDF print | E |
| I7 | `weakener_focus` with a non-factor `affectedNode` | execution agent, grep | F |
| I8 | Major / minor / OFI grading rule (ISO/IEC 17021-1, ISO/IEC 42006) | Vishnu | report wording, v0.7 |

## 13. What this spec does not do

It does not grade findings as major or minor. It does not predict an audit outcome. It does not import the
Statement of Applicability, the impact assessments, or the internal audit records. It does not use any
content from the workbook that taught the shape.
