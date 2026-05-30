# UofA Surrogate-Credibility Proto-Taxonomy

**Doc version:** v0.1 (draft)
**Derived from:** Jakeman, Barba, Martins, O'Leary-Roseberry, *Verification and Validation for Trustworthy Scientific Machine Learning*, arXiv:2502.15496 (2025).
**Role:** Declared coverage reference for Phase D of the surrogate pack (`UofA_Surrogate_Pack_Spec_v0_1.md` §8). Emerging reference, not canonical.
**Status:** UofA implementation artifact. Not a praxis contribution. No Cohen's-κ-against-canonical-taxonomy claim is made.

---

## 1. Purpose and role

This document is the reference set the surrogate pack's coverage matrix (Phase D) validates against. It answers, for the surrogate domain, the third question UofA exists to make answerable: how do you know the weakener catalog is comprehensive? Coverage is measured as the fraction of these reference defeaters that an implemented or reused pattern detects, with the remainder reported as documented gaps.

This is an **emerging reference**, used deliberately and with a stated caveat (§6). It is not a settled standard. It is adequate for tool implementation precisely because the coverage claim is "coverage against a declared, citable framework," not "coverage of a canonical taxonomy."

## 2. Provenance of the reference

The source is a recommendations framework from a Sandia-led group in the Oberkampf V&V lineage. It organizes 16 recommendations across four components: problem definition, verification, validation, and continuous credibility building. Its four-domain construct (verification, calibration, validation, and application domains, with an explicit region outside intended use) maps directly onto the surrogate pack's training-envelope and extrapolation framing.

Cross-anchors: ASME VVUQ 20-2009, ASME V&V 40-2018, and Oberkampf-Trucano-Pilch Predictive Capability Maturity Model (PCMM, SAND2007), which also grounds the pack's MRL usage.

OPAL-surrogate (arXiv:2403.08901) is **not** used as a coverage reference. It is a Bayesian surrogate-discovery and credibility-assessment method, a source of machinery, not an enumeration of defeaters. It is cited as method support, the same role CLARISSA plays in the existing UofA work.

## 3. Inversion method

Each recommendation states a practice to perform. The proto-taxonomy inverts each into the **defeater** that arises when the corresponding evidence is missing. Every defeater is phrased as an evidence-completeness failure: the relevant evidence is absent, or declared-but-unlinked. None is a correctness judgment. UofA checks that the evidence is present, linked, and auditable, never that the surrogate is accurate or the physics correct.

Defeater IDs live in their own namespace (`D-PD-*`, `D-VER-*`, `D-VAL-*`, `D-CCB-*`) keyed to the source recommendation number. They are deliberately decoupled from UofA pattern IDs, so the reference does not imply a commitment to implement a rule for every entry.

Coverage status legend:
- **COVERED** — an implemented or reused pattern detects this dimension.
- **PARTIAL** — a pattern covers part; a slice remains a gap.
- **GAP** — recognized dimension, no pattern yet, reported as uncovered.
- **CANDIDATE** — a named gap-probe target (method-first), not yet implemented.

## 4. The proto-taxonomy

### Component A — Problem Definition

| ID | Defeater (evidence-completeness phrasing) | UofA pattern | Status |
|---|---|---|---|
| D-PD-01 | Surrogate purpose, intended use, and declared limitations not stated in or linked to the COU | core COU / context-of-use | COVERED |
| D-PD-02 | Training/operating envelope not declared, or evaluation domain not distinguished from the validated domain (no basis to detect extrapolation) | W-ON-02 (presence), W-SURR-03 (containment) | COVERED |
| D-PD-03 | Quantities of interest the surrogate must predict not declared or scoped to the COU | core COU (QoI) | COVERED |
| D-PD-04 | Governing physical constraints/invariances the surrogate must respect not declared; model-structure rationale not documented | W-SURR-01 (constraint-evidence slice) | PARTIAL (structure rationale is GAP) |

### Component B — Verification

| ID | Defeater | UofA pattern | Status |
|---|---|---|---|
| D-VER-05 | Code-verification evidence (idealized/manufactured-solution tests on data independent of training) absent or unlinked | none | GAP |
| D-VER-06 | Solution-verification evidence absent; benchmark set does not span the application domain; residuals against reference not linked | W-SURR-04 (benchmark-coverage-gap), residuals-unlinked | CANDIDATE (SIP-enabled) |

### Component C — Validation

| ID | Defeater | UofA pattern | Status |
|---|---|---|---|
| D-VAL-07 | Calibration evidence and calibration-data provenance (distinct from training data) absent or unlinked | none | GAP |
| D-VAL-08 | Validation against purpose-specific acceptance criteria using independent data absent; metric not tied to declared purpose | core acceptance-criteria / decision | PARTIAL (validation-data independence is GAP) |
| D-VAL-09 | Prediction UQ absent, only a single error source reported, or extrapolation/structure uncertainty not propagated to the application domain | W-AL-02, `surrogateUQMethod` | COVERED |

### Component D — Continuous Credibility Building

| ID | Defeater | UofA pattern | Status |
|---|---|---|---|
| D-CCB-10 | Training/benchmark data fidelity, bias, noise, and vintage not documented | W-EP-03 (vintage), `hasBenchmarkProvenance` | PARTIAL (fidelity/bias is GAP) |
| D-CCB-11 | Data-processing procedures (normalization, abnormal/missing-data handling, transformations) not documented | none | GAP |
| D-CCB-12 | Sensitivity to optimization randomness (seed, initialization, regularization) not reported | W-AL-02 (sensitivity slice) | COVERED |
| D-CCB-13 | Hyperparameter selection/tuning procedure not documented; model-configuration provenance incomplete | W-AR-04 (version/config) | PARTIAL (tuning procedure is GAP) |
| D-CCB-14 | Reproducibility artifacts (source, trained weights, environment, repro scripts) and SQA evidence absent | core signing / PROV-DM | PARTIAL (SQA/repro completeness is GAP) |
| D-CCB-15 | No comparison of the surrogate against alternative SciML models or a CSE baseline using purpose-specific metrics | none | GAP |
| D-CCB-16 | Interpretability/explanation evidence for the surrogate's prediction mechanism absent | none | GAP |

### Beyond the reference: a defeater Jakeman does not enumerate

| ID | Defeater | UofA pattern | Status |
|---|---|---|---|
| D-X-01 | Surrogate credibility inherited from a high-fidelity parent model that was Not Accepted or has no recorded decision for the relevant COU | W-SURR-02 | COVERED |

The source touches lower-fidelity-data bias under recommendation 10 but does not treat credibility inheritance from a parent model as a distinct defeater. UofA surfaces it via the PROV-DM chain and the parent snapshot. This is a point where the tool's coverage exceeds the reference, and a candidate contribution back to the reference framework if this is ever written up.

## 5. Coverage summary

Of the 16 reference dimensions: 5 COVERED in full (D-PD-01, 02, 03, D-VAL-09, D-CCB-12), 1 CANDIDATE (D-VER-06, SIP-enabled), 5 PARTIAL (D-PD-04, D-VAL-08, D-CCB-10, 13, 14), and 5 GAP (D-VER-05, D-VAL-07, D-CCB-11, 15, 16). Plus one dimension (D-X-01) covered beyond the reference.

This is the intended shape of a coverage report: not 100 percent, with the uncovered dimensions named and traceable. The GAP and PARTIAL entries are the method-first gap surface for future patterns, not failures of the catalog.

## 6. Caveats and limitations

- The source explicitly disclaims comprehensiveness: the authors do not claim the four components or the recommendations are comprehensive or universally applicable, and aim to stimulate community development of SciML standards. Coverage reporting against this set must carry that caveat verbatim in substance.
- The inversion from practice to defeater is interpretive. Recommendations 1, 3, and 8 map onto core UofA COU/acceptance machinery rather than surrogate-specific patterns, so coverage of them is partly inherited from the core engine.
- Recommendations 9 and 14 overlap UofA's existing UQ and provenance machinery; the surrogate-specific slice is what the pattern must add.
- This proto-taxonomy is versioned. If a settled surrogate-credibility taxonomy emerges (community standard, ASME/NAFEMS working-group output), the coverage reference should migrate to it and this document retired or re-anchored.

## 7. How Phase D uses this

1. Treat §4 as the fixed reference set for the coverage matrix.
2. For each defeater, record whether an implemented or reused pattern detects it (dual-detection where applicable), producing COVERED / PARTIAL / GAP per row.
3. Emit the coverage report with the §6 caveat and the GAP/PARTIAL list as named, traceable uncovered dimensions.
4. Do not implement a pattern for every GAP. GAPs are documented coverage, and candidate gap-probe targets are promoted only through the pack's method-first validation, not pre-built to inflate coverage.

## 8. References

- Jakeman, Barba, Martins, O'Leary-Roseberry, arXiv:2502.15496 (2025). Source framework. (Co-author L. A. Barba, George Washington University.)
- Singh, Farrell-Maupin, Faghihi, OPAL-surrogate, CMAME / arXiv:2403.08901 (2024). Machinery, not coverage reference.
- ASME VVUQ 20-2009; ASME V&V 40-2018.
- Oberkampf, Trucano, Pilch, Predictive Capability Maturity Model, SAND2007-5948.
- Companions: `UofA_Surrogate_Pack_Spec_v0_1.md`, `SIP_Evidence_Contract_Spec_v0_1.md`, `SURROGATE_SIP_BUILD_HANDOFF.md`.
