# Surrogate Pack — Coverage Matrix (Phase D)

**Reference set:** `docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md` (16 defeaters
inverted from Jakeman et al., arXiv:2502.15496, plus `D-X-01` beyond the
reference). **Coverage target ≥ 70% is *not* asserted here.**

## How coverage is reported (and what it is not)

This matrix answers "how do you know the surrogate-credibility catalog is
comprehensive?" by reporting, for each reference defeater, whether an
implemented or reused pattern detects it — via the **C3** weakener path, the
**OOS** bundle-sufficiency path, or neither. Coverage is the **fraction of
reference defeaters detected**, with the remainder named as traceable gaps.

This is **not** a Cohen's-κ claim. Unlike the ISO 42001 pack (which validated
its catalog against the settled NIST AI RMF GOVERN taxonomy at κ), the
surrogate domain has **no settled taxonomy**. The proto-taxonomy is an
*emerging reference*, used deliberately and with the caveat below. No
inter-rater-κ-against-a-canonical-taxonomy claim is made.

## Emerging-reference caveat (carried from proto-taxonomy §6, in substance)

> The source explicitly disclaims comprehensiveness: the authors do not claim
> the four components or their recommendations are comprehensive or universally
> applicable, and aim to stimulate community development of SciML standards.
> Coverage reporting against this set carries that caveat. The
> practice-to-defeater inversion is interpretive. If a settled
> surrogate-credibility taxonomy emerges (a community standard, ASME/NAFEMS
> working-group output), the coverage reference should migrate to it and this
> document be retired or re-anchored.

## Dual-detection matrix

Legend — **C3**: structural weakener (Jena/derivation). **OOS**: productive
bundle-sufficiency (judgment-required gap surfaced, not penalized).
Status: COVERED / PARTIAL / GAP / CANDIDATE (method-first, not pre-implemented).

### Component A — Problem Definition

| ID | Defeater (evidence-completeness) | C3 path | OOS path | Status |
|---|---|---|---|---|
| D-PD-01 | Purpose/intended-use/limitations not stated or linked | core COU | — | COVERED |
| D-PD-02 | Envelope undeclared / eval domain not distinguished | W-ON-02 (presence), W-SURR-03 (containment) | — | COVERED |
| D-PD-03 | QoIs not declared / scoped to the COU | core COU (QoI) | — | COVERED |
| D-PD-04 | Governing constraints undeclared; model-structure rationale undocumented | W-SURR-01 (constraint-evidence slice) | — | PARTIAL (structure rationale GAP) |

### Component B — Verification

| ID | Defeater | C3 path | OOS path | Status |
|---|---|---|---|---|
| D-VER-05 | Code-verification evidence absent/unlinked | — | — | GAP |
| D-VER-06 | Solution-verification absent; benchmark doesn't span domain; residuals unlinked | W-SURR-04 *(candidate)*, residuals-unlinked *(candidate)* | — | CANDIDATE (SIP-enabled) |

### Component C — Validation

| ID | Defeater | C3 path | OOS path | Status |
|---|---|---|---|---|
| D-VAL-07 | Calibration evidence + calibration-data provenance absent/unlinked | — | **OOS-SURR-CALIBRATION** | PARTIAL (OOS surfaces; no C3) |
| D-VAL-08 | Validation vs purpose-specific criteria on independent data absent | core acceptance-criteria / decision | — | PARTIAL (data-independence GAP) |
| D-VAL-09 | Prediction UQ absent / single error source / extrapolation uncertainty not propagated | W-AL-02, `surrogateUQMethod` | — | COVERED |

### Component D — Continuous Credibility Building

| ID | Defeater | C3 path | OOS path | Status |
|---|---|---|---|---|
| D-CCB-10 | Data fidelity/bias/noise/vintage undocumented | W-EP-03 (vintage), `hasBenchmarkProvenance` | — | PARTIAL (fidelity/bias GAP) |
| D-CCB-11 | Data-processing procedures undocumented | — | — | GAP |
| D-CCB-12 | Sensitivity to optimization randomness unreported | W-AL-02 (sensitivity slice) | — | COVERED |
| D-CCB-13 | Hyperparameter/tuning provenance incomplete | W-AR-04 (version/config) | — | PARTIAL (tuning procedure GAP) |
| D-CCB-14 | Reproducibility artifacts + SQA evidence absent | core signing / PROV-DM | — | PARTIAL (SQA/repro completeness GAP) |
| D-CCB-15 | No comparison vs alternative SciML / CSE baseline | — | **OOS-SURR-COMPARISON** | PARTIAL (OOS surfaces; no C3) |
| D-CCB-16 | Interpretability/explanation evidence absent | — | — | GAP |

### Beyond the reference

| ID | Defeater | C3 path | OOS path | Status |
|---|---|---|---|---|
| D-X-01 | Credibility inherited from a Not-Accepted / undecided parent | W-SURR-02 | — | COVERED (exceeds reference) |

## Summary

Of the 16 reference dimensions:

- **5 COVERED** — D-PD-01, D-PD-02, D-PD-03, D-VAL-09, D-CCB-12
- **7 PARTIAL** — D-PD-04, D-VAL-07, D-VAL-08, D-CCB-10, D-CCB-13, D-CCB-14, D-CCB-15
  (D-VAL-07 and D-CCB-15 are PARTIAL *because the OOS path surfaces them* as
  judgment-required gaps, even with no C3 structural detector)
- **1 CANDIDATE** — D-VER-06 (SIP-enabled; method-first, not pre-implemented)
- **3 GAP** — D-VER-05, D-CCB-11, D-CCB-16
- Plus **D-X-01** covered beyond the reference.

**Fraction detected (COVERED=1, PARTIAL=0.5, CANDIDATE/GAP=0):**
`(5×1 + 7×0.5) / 16 = 8.5 / 16 ≈ 53%`, with every uncovered dimension named and
traceable. This is the intended shape of a coverage report — not 100%, with the
GAP/PARTIAL entries forming the method-first surface for future patterns, not
failures of the catalog. Adding the two OOS detectors moved D-VAL-07 and
D-CCB-15 from GAP to PARTIAL relative to the proto-taxonomy's own §5 tally.

The CANDIDATE and GAP rows are **not** to be back-filled with pre-built rules to
inflate this number; candidates are promoted only through the coverage method.
