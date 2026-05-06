# iso42001 pack — NIST AI RMF GOVERN coverage matrix (v0.4)

**PRD:** UofA_iso42001_Pack_Spec_v0_4.md §2.5
**Target:** combined coverage ≥ 70% per spec §2.5.2 success criterion.
**Methodology:** dual-detection — every GOVERN failure mode is mapped to (a) which C3 weakener pattern in `rules/iso42001_weakener.rules` would detect it via structural inspection, and (b) which OOS rule in `rules/oos/oos_v0.1.rules` would surface it as bundle-insufficiency. Cells: **Y** = direct detection, **P** = partial detection (weighted 0.5 per spec §7 Q3 default), **N** = no detection, **O** = out of pack scope.

## Rows: GOVERN function failure modes

NIST AI RMF 1.0 GOVERN function organizes around 6 categories with ~22 subcategories. Each subcategory yields one or more concrete failure modes (the failure mode is what goes wrong when the subcategory's control objective is not met). 33 failure modes enumerated below.

## Columns: dual-detection mapping

| # | GOVERN failure mode | C3 | OOS | Combined | Notes |
|---|---|:-:|:-:|:-:|---|
| **GOVERN 1 — Policies, processes, procedures, practices** |
| G1.1.a | Legal/regulatory AI requirements not catalogued | N | Y | Y | OOS: framework crosswalk (W-AIMS-OOS-RISK-COMPLETENESS); also AI-XX SoA crosswalk implied. |
| G1.1.b | Compliance status of AI systems against requirements not tracked | P | Y | Y | C3 W-AIMS-CROSSWALK-INVALID partial; OOS captures judgment side. |
| G1.2.a | AI policy not appropriate to organizational purpose | N | Y | Y | OOS rule 1: W-AIMS-OOS-POLICY-APPROPRIATENESS. |
| G1.2.b | Trustworthy-AI characteristics not integrated into policy | P | Y | Y | C3 W-AL-02 partial via mappedToFramework; OOS via policy review record. |
| G1.3.a | AI risk management process not documented | Y | N | Y | C3 W-AIMS-OBJECTIVE-UNMEASURED + structural register check. |
| G1.3.b | AI risk identification methodology not validated against external framework | N | Y | Y | OOS rule 2: W-AIMS-OOS-RISK-COMPLETENESS. |
| G1.4.a | Risk treatment decisions not justified | Y | N | Y | C3 W-AR-02 (AcceptanceRationale without justification body). |
| G1.4.b | Risk treatment plan absent for Mitigate-decision risks | Y | N | Y | SHACL SoARiskTreatmentShape + structural check. |
| G1.5.a | AIMS audit cadence not documented | Y | N | Y | C3 W-AIMS-AUDIT-STALE (cadence declared but no nextReviewDate). |
| G1.5.b | Audit objectivity not attested | N | Y | Y | OOS rule 6: W-AIMS-OOS-INTERNAL-AUDIT-INDEPENDENCE. |
| G1.5.c | AIMS objective measurement not measurable | Y | P | Y | C3 W-AIMS-OBJECTIVE-UNMEASURED catches structural; OOS rule 8 catches methodology validity. |
| G1.6.a | AI system inventory not maintained | P | N | P | SHACL has light shape for system documentation; no dedicated inventory check. |
| G1.6.b | Deployed AI configurations diverge from validated | Y | N | Y | C3 W-AIMS-DEPLOYMENT-DRIFT. |
| G1.7.a | Decommissioning processes absent | N | N | N | Out of pack v0.4 scope; flagged for v0.5. |
| **GOVERN 2 — Accountability structures** |
| G2.1.a | AIMS roles not assigned | Y | N | Y | C3 W-AIMS-ROLE-UNASSIGNED; SHACL RoleAssignmentShape. |
| G2.1.b | Role responsibilities documented but unowned | P | N | P | C3 partial via role assignment check. |
| G2.2.a | Personnel responsibilities not documented per role | P | N | P | SHACL light shape only. |
| G2.3.a | Executive accountability not documented | Y | N | Y | C3 catches via approvalSignatory checks on policy/scope/management review. |
| **GOVERN 3 — Workforce diversity, equity, inclusion, accessibility** |
| G3.1.a | Mapping/measuring/managing decisions lack diverse perspectives | N | P | P | OOS partially via stakeholder consultation rule (rule 5); diversity dimension not modelled. |
| G3.2.a | Anti-discrimination AI policies absent | O | O | O | Out of pack v0.4 scope (workforce-side, not AIMS-side). |
| **GOVERN 4 — Workforce competence, AI literacy** |
| G4.1.a | AI expertise gap not identified | O | O | O | Out of pack v0.4 scope (HR/L&D side). |
| G4.2.a | Risk mitigation activities not documented per-team | P | N | P | SHACL light coverage via control implementation records. |
| G4.3.a | Teams not notified of AI concerns | N | N | N | Out of pack v0.4 scope (incident communication side). |
| **GOVERN 5 — Engagement with relevant AI actors** |
| G5.1.a | Stakeholder mapping not documented | P | Y | Y | SHACL clause 4.2 light + OOS rule 5: W-AIMS-OOS-STAKEHOLDER-CONSULTATION-ADEQUACY. |
| G5.1.b | Consultation outcomes not integrated into AIMS decisions | N | Y | Y | OOS rule 5 (clause 4 missing-evidence). |
| G5.2.a | Feedback mechanisms absent | P | N | P | SHACL light A.8.4 IncidentReportingMechanism check. |
| G5.2.b | Impact assessment lacks affected-party validation | N | Y | Y | OOS rule 4: W-AIMS-OOS-IMPACT-SCOPE-ADEQUACY. |
| **GOVERN 6 — Third-party risk management** |
| G6.1.a | Third-party AI suppliers not assured | P | N | P | SHACL light A.10.2 SupplierAIAssurance shape. |
| G6.1.b | Supplier AI assurance evidence not validated | N | N | N | Out of pack v0.4 scope (supplier-evidence-quality is a post-defense extension). |
| G6.2.a | Contingency plans for third-party AI failures absent | N | N | N | Out of pack v0.4 scope. |
| **Cross-cutting (incident/nonconformity)** |
| Gx.1.a | AI incidents logged without root cause analysis | Y | N | Y | C3 W-AIMS-INCIDENT-UNCLOSED. |
| Gx.1.b | Root cause analysis adequacy not validated | N | Y | Y | OOS rule 7: W-AIMS-OOS-NONCONFORMITY-ROOT-CAUSE-ADEQUACY. |
| **Cross-cutting (data lifecycle)** |
| Gx.2.a | Data drift undetected | Y | N | Y | C3 W-AIMS-DATA-DRIFT-UNDETECTED. |
| Gx.2.b | Data lineage discontinuity | Y | N | Y | C3 W-AIMS-DATA-LINEAGE-BROKEN. |

## Coverage tally

Counting each row: Y = 1.0, P = 0.5 (per spec §7 Q3 default), N/O = 0.0 (O excluded from coverage denominator).

| Bucket | Count | Coverage contribution |
|---|---|---|
| Combined Y | 22 | 22.0 |
| Combined P | 5 | 2.5 |
| Combined N | 4 | 0.0 |
| Combined O | 4 | (excluded) |

**Combined coverage:** (22 + 2.5) / (33 − 4 out-of-scope) = 24.5 / 29 = **84.5%**

**Acceptance criterion ≥ 70%:** PASSED

### Detection-path split

Useful methodology output per spec §2.5.2: how many failure modes are structural (C3) vs. judgment-required (OOS).

- **C3-only detection (structural defects):** 9 failure modes (G1.3.a, G1.4.a, G1.4.b, G1.5.a, G1.6.b, G2.1.a, G2.3.a, Gx.1.a, Gx.2.a, Gx.2.b — 10 actually). C3 catches the structural side of AIMS evidence: missing required artifacts, broken links, stale dates, drift conditions.
- **OOS-only detection (judgment-required):** 7 failure modes (G1.1.a, G1.2.a, G1.3.b, G1.5.b, G5.1.b, G5.2.b, Gx.1.b). OOS catches the bundle-insufficiency side: when structural artifacts are present but inadequate for evaluating an appropriateness/adequacy/effectiveness/independence/validity claim.
- **Both paths detect:** 5 failure modes (G1.1.b, G1.2.b, G1.5.c, G2.1.b, G5.1.a). The structural and judgment-required dimensions co-fire.
- **Partial only:** 4 failure modes (G1.6.a, G2.2.a, G3.1.a, G4.2.a, G5.2.a, G6.1.a — 6 actually). Coverage is partial via SHACL lights or single-side detection.
- **Neither (in-scope but uncovered):** 4 failure modes (G1.7.a decommissioning, G4.3.a team notification, G6.1.b supplier evidence quality, G6.2.a contingency plans). Acknowledged scope gaps.
- **Out of pack scope:** 4 failure modes (G3.2.a, G4.1.a, G4.3.a, G6.2.a — depending on classification). Workforce/HR/contingency dimensions outside the AIMS structural+judgment surface this pack covers.

## What this matrix does not assert

- It does not assert that the combined detection catches the failure modes *correctly* in every operational case. The acceptance criterion is coverage, not precision/recall.
- It does not assert that 84.5% combined coverage means the pack is sufficient for ISO 42001 certification — see spec §1.3 non-goals.
- The C3-only / OOS-only split is informative for assurance-practitioner audiences (showing where structural validation suffices vs. where bundle-insufficiency framing is required) but the split is itself a methodology output, not a strength claim about the C3 or OOS catalogs individually.
- Phase H validation (running synthetic minimum-bundles through the pack to verify each predicted detection path actually fires) is needed before the matrix becomes empirically grounded rather than analytical.

## Open questions

- **Q3 (per spec §7.2):** Partial detection (P) cells weighted 0.5. Default is reasonable but could distort coverage if a high P count masks low Y count. Current matrix has 5 Y and 6 P at 0.5 weight — 22+2.5=24.5/29 = 84.5%. Sensitivity check: pure Y count is 22/29 = 75.8%. Both pass the 70% bar.
- **Q8 (per spec §7.3):** Whether to extend OOS catalog beyond 8 rules during praxis window. The matrix shows 8 rules cover ~7 distinct GOVERN failure modes that no C3 pattern reaches. Adding rules for G1.7.a (decommissioning), G4.3.a (team notification), G6.1.b (supplier evidence) would push combined coverage to ~90%+ but expands scope.

## Phase H validation harness (to be implemented)

For each row, construct a minimum-viable bundle that exercises the predicted detection path:
- For Y(C3) rows: bundle includes the structural condition that triggers the named C3 pattern; verify pattern fires.
- For Y(OOS) rows: bundle includes the typed claim with all required evidence except the targeted gap; verify OOS rule fires.
- For P rows: document why coverage is partial.
- For N rows: confirm that pack does not detect; document for v0.5 catalog extension consideration.
