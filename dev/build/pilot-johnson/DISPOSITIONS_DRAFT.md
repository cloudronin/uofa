# Candidate dispositions — DRAFT

**Every row below is DRAFT. Nothing here is adjudicated.** Spec §0 and §3: this
session drafts candidates with the source text that supports them; the author
decides, later, under the written protocol. Rows marked JUDGMENT-CLASS are
explicitly not resolved.

Input: `uofa rules dev/build/pilot-johnson/johnson-pilot.jsonld` → **12 weakeners,
6 patterns** (11 High, 1 Medium). Full output in `rules-report.txt`.

## The question the outline does not answer, raised before the table

Nine of these twelve firings are true of the **package** and false of the
**source**. The paper documents a sensitivity analysis, names its comparators,
and states its operating envelope four separate ways; the workbook has nowhere to
put any of them, so the rules correctly report their absence from the encoding.

That splits the disposition question in two, and the protocol outline's §4 does
not say which one a disposition answers:

> **Does a disposition adjudicate the weakener against the source, or against the
> package?**

Against the source, "the assessment documented sensitivities at p.22" makes the
firing Not Accepted. Against the package, a reviewer holding the JSON-LD has no
sensitivity analysis and the firing is a true and useful warning, so it is
Accepted. Dispositioning on the source reading would suppress a warning that is
correct about the artifact the reviewer actually receives.

The table below gives **both readings** where they differ and marks the row
JUDGMENT-CLASS. Filed as the lead §4 finding.

---

## Dispositions

| # | Pattern / factor | Candidate verdict | Source anchor | Rule as applied | Confidence note |
|---|---|---|---|---|---|
| D-01 | **W-AL-02** [Medium] ×1 — UQ reported, no documented sensitivity analysis | **JUDGMENT-CLASS.** Not Accepted against the source; Accepted against the package | p.22 [M&S 30] "Penetration depth is sensitive to both particle velocity and orientation at impact"; p.25 Results Robustness 4 "Sensitivities captured in quantitative model, including for combination of factors (interaction)" | Not Accepted against the source because the source states the sensitivity result at p.22 and rates a factor on it at p.25. No testable rule decides the package reading. | The encoding cannot carry it: `uofa:SensitivityAnalysis` is a schema class with a shape, and it appears nowhere in `excel_constants.py`, `excel_reader.py` or `excel_mapper.py`. See F-3 |
| D-02 | **W-AR-05** [High] — `independent-duplicate-regression-analysis` has no comparator link | **Not Accepted** | p.18 4.1.3 b(3) "Duplicate analysis using competitive software performed by reviewer; resulting model is identical" | Not Accepted because the source names the comparator at [anchor]: an independent commercial statistics package. | The comparator was written as prose in `Compares To`, which expects a URI; import logged it as a non-well-formed subject and dropped it |
| D-03 | **W-AR-05** [High] — `output-comparison-to-test-data…` has no comparator link | **Not Accepted** | p.21 [M&S 28](3) "Output graphically compared to test data"; p.22 tolerance bound 0.128 cm | Same rule as D-02: the source names the comparator, the DOE test data. | As D-02 |
| D-04 | **W-AR-05** [High] — `conceptual-validation-via-sme-team-review` has no comparator link | **Not Accepted** | p.17 [M&S 17] "presentation to the test team and anomaly team leads and exercise of the model calculator in real time" | Same rule as D-02: the comparator is SME engineering judgment, named at [anchor]. | Comparator is a human judgment, not an entity a URI naturally identifies. See F-4 |
| D-05 | **W-AR-05** [High] — `independent-technical-review-of-model-and-analysis` has no comparator link | **Not Accepted** | p.10 [M&S 36]; p.24 [M&S 36] "reviewed by two NASA statisticians … independently by engineers" | Same rule as D-02. | As D-04. A review activity arguably has no comparator at all, which may make the rule mis-scoped for `ReviewActivity` — see F-4 |
| D-06 | **W-AR-05** [High] — `waived-validation-against-real-world-system-data` has no comparator link | **ACCEPTED** | p.19 4.1.2 c "No model confirmation/validation using independent data planned or performed … No RWS data available for validation"; p.25 Validation 1 | **Accepted because the source states at [anchor] that no comparator data exists.** | The one firing in this set that is unambiguously right, on both readings. It is the paper's own most conservative disclosure, restated by the engine |
| D-07 | **W-CON-01** [High] — `Numerical code verification`: assessed, no level, decision Accepted | **ACCEPTED** | evidence p.18 4.1.3 b(3); absent level per AMBIGUITY_LOG A-06 | **Accepted because the package declares outcome Accepted while this factor carries evidence and no level**, the level being unstateable across the 7009A 0-4 → V&V 40 1-5 boundary. | Would NOT have fired on the raw extraction, which synthesized 4/4 here. The honest encoding raises the weakener; the confident one hides it |
| D-08 | **W-CON-01** [High] — `Model form`: assessed, no level | **ACCEPTED** | evidence p.17 [M&S 17]; A-06 | Same rule as D-07. | As D-07 (raw extraction had 3/3) |
| D-09 | **W-CON-01** [High] — `Output comparison`: assessed, no level | **ACCEPTED** | evidence p.19; A-06 | Same rule as D-07. | As D-07 (raw extraction had 4/4). Note 7009A rates Validation 1 where the extractor put 4 |
| D-10 | **W-NASA-03** [High] — Process management assessed, no linked ProcessAttestation | **ACCEPTED** | p.25 M&S Process/Product Management 4: "Standard formal experimental design and data analysis process rigorously followed and documented in standard form … All review comments addressed" | Accepted because the package carries no `ProcessAttestation` node, and the rule tests the package. | **Repairable in encoding, unlike D-01.** `ProcessAttestation` IS in the workbook's evidence-type list; neither the extractor nor the review pass created one. Raises F-5: may a review pass ADD evidence rows, or only correct emitted ones? |
| D-11 | **W-NASA-06** [High] — Results robustness assessed, no linked SensitivityAnalysis | **JUDGMENT-CLASS.** Not Accepted against the source; Accepted against the package | p.22 [M&S 30]; p.25 Results Robustness 4 | As D-01. | Not repairable through the on-ramp at all — same root cause as D-01 |
| D-12 | **W-ON-02** [High] — COU has neither applicability constraint nor operating envelope | **JUDGMENT-CLASS.** Not Accepted against the source; Accepted against the package | p.19 [M&S 14] "Model specific to this tire and inflation system design. Model may not apply to redesigned inflation system"; p.19 [M&S 18] domain of validation; p.18 [M&S 16] domain of verification; p.23 [M&S 26] limits of operation | Not Accepted against the source because the source states the envelope four separate ways at [anchor]. | **Known observation, not a new finding.** `UofA_Ch4_Numbers_and_Repairs_Spec_v1_0.md` §4.1 records W-ON-02 firing on 65/71 queue packages and asks for verification against canonical encodings. Morrison COU1 fires it too. This pilot is one such verification |

## Factors the pack expects a disposition on but the engine raised nothing for

Recorded because silence is not the same as a clean bill, and the done-gate asks
for a disposition per factor as well as per firing.

- **The 14 factors carrying no level** (all 13 V&V 40 factors plus `Development
  technical review`) have status and anchored rationale but no level, per A-06 and
  the anchored-fan-out ruling. Only the three marked `assessed` drew a weakener
  (D-07 to D-09). The eleven marked `not-assessed`, `scoped-out` or
  `not-applicable` are silent because W-CON-01 excludes those statuses by design.
  **Candidate disposition: Not Applicable** for all eleven, on the rule that a
  factor the source never assessed has no requirement to be based against. Note
  this means the honest encoding's largest gap is the one the engine says least
  about.
- **`Input pedigree`** draws nothing because the factor does not exist in the
  pack. Predeclared 3, achieved 3 in the source (p.25). **No disposition is
  possible.** ESCALATION A-07, INV-20 territory.
- **W-AR-02** (achieved below required, yet Accepted) did **not** fire, correctly:
  achieved ≥ required on all five levelled factors, which is the paper's own
  claim. Worth stating because it is the one place the encoding successfully
  carries Johnson's headline — and it does so only because the review pass
  restored the predeclared column from Table 3's shading. On the raw extraction
  the same rule would also not have fired, but for the wrong reason: required had
  been set equal to achieved everywhere.

## Summary for the author's review pass

| Verdict class | Count |
|---|---|
| Accepted | 5 (D-06 to D-10) |
| Not Accepted | 4 (D-02 to D-05) |
| JUDGMENT-CLASS, not resolved | 3 (D-01, D-11, D-12) |
| Not Applicable (factors, no firing) | 11 |
| No disposition possible (schema gap) | 1 (`Input pedigree`) |

Of the twelve firings, **one** (D-06) describes a limitation of the underlying
assessment. **Three** (D-07 to D-09) describe a real property of this encoding
that exists only because the pilot refused to invent levels. **Eight** describe
things the workbook cannot carry.
