# Candidate dispositions — aero COU2

**ADJUDICATED by the author, 2026-08-21.** Drafted under `docs/Encoding_Protocol_v0_1.md` Part B plus the
author's Johnson rulings as precedent. Both questions the draft raised were ruled on
2026-08-21; no AUTHOR-RULE rows remain. The rulings are in `AUTHOR_SUMMARY_COU2.md` §4.

Package `aero-cou2.jsonld`, re-imported after the cell walk. `uofa rules` reports
**16 weakeners across 8 patterns** (14 High, 2 Medium). The count rose from 15 for the same
reason as COU1: clearing the template placeholder gave the MMS node a well-formed identifier,
so `W-AR-05` reaches it.

**This package's decision outcome is `Not accepted`** — the first such record committed
anywhere in the project, and the case Part B has been waiting on for its
Not-Applicable-versus-Overruled worked example. Queued for v0.2 in
`docs/protocol-v0_2-notes.md`.

## Dispositions

| # | Pattern | Node | Verdict | Class | Rule as applied | Precedent |
|---|---|---|---|---|---|---|
| A2-01 | W-AR-05 [High] | `mms-code-verification-inherited-from-cou1` | **Confirmed** | mechanical | Confirmed because no resolvable `comparedAgainst` is carried. Source names "Analytical MMS benchmark solutions"; dropped at expansion as a non-well-formed subject. | Johnson D-02; SF-5 |
| A2-02 | W-AR-05 [High] | `mesh-convergence-at-mid-span-inherited-from-cou1` | **Confirmed** | mechanical | As A2-01. "Multiple mesh refinement levels" dropped. | Johnson D-02; SF-5 |
| A2-03 | W-AR-05 [High] | `cascade-rig-validation-reuse-for-cruise-assessment` | **Confirmed** | mechanical | As A2-01. The comparator is written as a filename, `cascade_rig_temperature_data.csv (take-off conditions)`, which is not a URI and is dropped. A filename is the sharpest SF-5 instance in either package: the source identifies the referent precisely and the schema still cannot hold it. | Johnson D-02; SF-5 |
| A2-04 | W-AR-05 [High] | `cruise-sensitivity-study` | **Confirmed** | mechanical | As A2-01. "Baseline nominal cruise case (Run #63 conditions)" dropped. | Johnson D-02; SF-5 |
| A2-05 | W-AR-05 [High] | `cruise-probabilistic-uq-monte-carlo-propagation` | **Confirmed**, *criterion-as-comparator form* | mechanical | Distinct from COU1's A1-05. Here `comparedAgainst` is `"Acceptance criterion peak temperature <= 1080K at P95"` — a **criterion**, not a referent entity, dropped at expansion. The source does state something the package cannot carry, so this is SF-5, but it widens SF-5's shape: the referent classes SF-5 proposes would need to cover an acceptance threshold as well as an artifact. | Johnson D-02; SF-5, extended |
| A2-06 | W-AL-02 [Medium] | the COU | **Confirmed** | mechanical | Confirmed because the package carries no `SensitivityAnalysis` node, though `sensitivity_study_cruise.csv` is in the bundle. On-ramp has no route. | Johnson D-01 |
| A2-07 | W-NASA-06 [High] | Results robustness | **Confirmed** | mechanical | Same missing root as A2-06. | Johnson D-10 |
| A2-08 | W-NASA-03 [High] | (factor, unnamed) | **Confirmed** | mechanical | Asserted factor carries no `uofa:hasEvidence` link, and no source-supported row clears it. | Part B, pack-specific → consistency |
| A2-09 | W-ON-02 [High] | the COU | **Confirmed** | mechanical | Neither applicability constraint nor operating envelope carried. **No per-package repair.** Sharper here than anywhere: the COU's whole finding is a regime mismatch — narrative §4.2, "The cascade (Re 1.20e6) is outside the cruise operating envelope (Re 0.85e6)" — and the envelope is exactly what the workbook cannot hold. | Johnson **D-11**; SF-6 |
| A2-10 | W-CON-04 [Medium] | the COU | **Confirmed** | mechanical | Package does not carry the referenced element. | Part B, consistency structural |
| A2-11 | W-NASA-02 [High] | (unnamed) | **Confirmed** | mechanical | Pack-specific pattern taking its core family's rule; named element absent. | Part B, pack-specific row |
| A2-12 | W-EP-04 [High] ×5 | (unnamed) | **Confirmed**, emphatically | judgment, author act | **RULED 2026-08-21**, under the same W-EP-04 rule applied to COU1 A1-13 — which is what makes it a rule rather than two decisions. At cruise-creep stakes, five risk-conditioned unassessed factors are precisely why the source's own answer is Not Accepted: **the firings and the decision agree.** The five are Model form, Test conditions, Equivalency of input parameters, Output comparison, Relevance of validation activities, which the source names as a single systematic gap with one root cause: §4.2 "The cascade (Re 1.20e6) is outside the cruise operating envelope (Re 0.85e6)"; §6 "Systematic applicability gap (single root cause, 5 Not Assessed factors)". | Part B, epistemic risk-conditioned; pairs with COU1 A1-13 |

**W-CON-01 does not fire**, as anticipated — no scale boundary exists in a bundle authored
against its own pack. **No compound patterns fire on COU2**, against six on COU1: the compounds
key on coexistence with `W-AR-02`, which cannot fire here because the decision is Not accepted
rather than Accepted-over-a-shortfall.

## Silence sweep, per §4e

Nineteen expected factors. **Five are `not-assessed`, and they are the substance of this
assessment** rather than an encoding gap — the source presents them as one systematic finding.

| Factor | Req / Ach | Status | Disposition |
|---|---|---|---|
| Software quality assurance | 2 / 2 | assessed | No disposition needed |
| Numerical code verification | 3 / 3 | assessed | No disposition needed |
| Discretization error | 3 / 3 | assessed | No disposition needed |
| Numerical solver error | 2 / 2 | assessed | No disposition needed. Narrative §6 confirms "Verification factors (1.1-1.5): all 5 Assessed at or above required level" |
| Use error | 2 / 2 | assessed | No disposition needed |
| **Model form** | 3 / — | **not-assessed** | Source-stated gap, §6 open item 1: "Not Assessed — no cruise-regime validation." Base of A2-12 |
| Model inputs | 3 / 3 | assessed | No disposition needed |
| Test samples | 2 / 2 | assessed | No disposition needed |
| **Test conditions** | 3 / — | **not-assessed** | Source-stated gap, §6 open item 2: "no cruise-Re test conditions." Base of A2-12 |
| **Equivalency of input parameters** | 3 / — | **not-assessed** | Source-stated gap, §6 open item 3. Base of A2-12 |
| **Output comparison** | 3 / — | **not-assessed** | Source-stated gap, §6 open item 4: "no cruise output measurements exist." Base of A2-12 |
| Relevance of the quantities of interest | 3 / 3 | assessed | No disposition needed |
| **Relevance of the validation activities to the COU** | 3 / — | **not-assessed** | Source-stated gap, §6 open item 5: "cascade outside cruise envelope." Base of A2-12, and the root the other four descend from |
| Data pedigree | 3 / 3 | assessed | No disposition needed |
| Development technical review | 3 / 3 | assessed | No disposition needed |
| Development process and product management | 3 / 3 | assessed | No disposition needed |
| Results uncertainty | 3 / 2 | assessed | No disposition needed. Shortfall carried with the source's model-form-uncertainty caveat |
| Results robustness | 2 / 2 | assessed | No disposition needed. Drew A2-07 |
| Use history | 2 / 1 | assessed | No disposition needed. Shortfall stated at §6 |
| *Film Cooling Validation* (narrative §4.3) | 3 / 1 | source-stated | **No pack factor exists.** The source scopes it as inherited from COU1 and "not a COU2-specific applicability finding". Declination recorded on row 17's rationale, logged as G-06 |

## Summary

| Class | Firings |
|---|---|
| Confirmed, mechanical | 11 |
| Confirmed, judgment (author act) | 5 |
| Not Applicable | 0 |
| Cascading compounds | 0 |
| **Total** | **16** |

## The decision — RULED 2026-08-21

**`Not accepted` stands as carried, and the symmetry with COU1 is the point.**

Same evidence family. Higher-stakes context of use — cruise creep-life rather than concept-stage
take-off screening. The source declines because the shortfalls that were tolerable for take-off
screening are disqualifying here, and COU1's board accepted the same evidence family with
conditions attached.

**Identical weaknesses, different contexts of use, opposite defensible decisions.** That is the
tier logic doing its one essential job, and it is why this pair is v0.2's second worked example
rather than COU2 alone.

**No Not Applicable verdicts.** As with COU1, all five evidence nodes are `ValidationResult`,
so SF-4's node-class exception finds nothing to apply to.
