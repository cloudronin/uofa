# Ambiguity log — Johnson encoding pilot

State: DRAFT. Every entry is re-adjudicated by the author in the review pass.
Spec §4. Entry shape: the ambiguity, the resolution this session chose for the
DRAFT, and the rule it applied choosing it.

An entry is mandatory whenever the source underdetermines a field: two plausible
readings, an implied value, a unit ambiguity, or a 7009A→7009B mapping that is not
mechanical. Rows marked **ESCALATION** are spec §6 cases — places the pack cannot
express what the paper states — and are *not* resolved here.

Entries A-01 through A-19 were opened during scoping and mapping, before
extraction. Later entries are appended as the extract-review pass raises them.

---

## Part 1 — the 7009A → 7009B mapping

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| A-01 | Johnson's `Uncertainty Characterization` vs the pack's `Results uncertainty`. The names differ and so does the emphasis: Johnson's factor is about characterising uncertainty, the pack's about uncertainty *of results*. | Map to `Results uncertainty`, carry the level unchanged (predeclared 4, achieved 4). | Both sit in the NASA-only block on the same 0-4 scale, and Johnson's achieved rationale ("Uncertainties fully characterized statistically", p.25) is a statement about results uncertainty. Rename, not re-scope. |
| A-02 | Johnson's `M&S History` vs the pack's `Use history`. | Map to `Use history`, level unchanged (3/3). | Same 0-4 block. Johnson's rationale is about the analysis code's prior use and the model's novelty (p.25), which is what `Use history` asks. |
| A-03 | Johnson's `M&S Process / Product Management` vs the pack's `Development process and product management`. | Map, levels unchanged (predeclared 2, achieved 4). | Same 0-4 block; the pack's name is the 7009B wording of the same factor. |
| A-04 | Johnson's `Verification` is one factor at one level. The pack splits verification across five V&V 40 factors on a 1-5 scale. | **Do not fan out the level.** Populate only the V&V 40 verification factors the worksheet answers in their own terms: `Numerical code verification` (p.18, "Commercial analysis code well-established … Duplicate analysis using competitive software performed by reviewer; resulting model is identical") and `Numerical solver error` (p.18, solution verification: "No. Not required"). `Software quality assurance`, `Discretization error`, `Use error` left blank and listed. | Anchored fan-out only (author ruling 2026-08-20). A cell is populated when the source answers *that* question, not when a coarser parent level can be divided. |
| A-05 | Johnson's `Validation` is one factor at Level 1. The pack splits validation across six V&V 40 factors on a 1-5 scale. | **Do not fan out.** Populate `Model form` from conceptual validation (p.17) and leave `Model inputs`, `Test samples`, `Test conditions`, `Equivalency of input parameters`, `Output comparison` blank and listed — the paper performed no empirical validation, so there is nothing to state about them beyond its absence, which the caveat records. | Same rule as A-04. |
| A-06 | The scale itself: 7009A factor levels run 0-4; the pack's 13 V&V 40 factors run 1-5. A level carried across is not the same quantity. | Levels are carried only within the 0-4 NASA block. No 7009A level is rewritten onto a 1-5 factor. | A unit change is an ambiguity, not a conversion. Nothing in the source licenses a mapping function between the two scales. |
| A-07 **ESCALATION** | `Input pedigree`. Johnson predeclares it at 3 and achieves 3 with a rationale (p.25). **The pack has no factor for it.** The nearest name, `Model inputs`, is a V&V 40 validation factor asking whether input data is accurate and well characterised — a different question, on a different scale. | **Not resolved.** Recorded as a schema finding. The value is not forced into `Model inputs`. | Spec §6: where the pack's vocabulary cannot express what the paper states, escalate. INV-20 territory. |
| A-08 **ESCALATION** | "Level 0". Table 3 carries "A lower level 0 indicates insufficient evidence to make a determination" (p.7). Level 0 exists on the 6 NASA factors and does not exist on any of the 13 V&V 40 factors (1-5). | **Not resolved.** Johnson uses no Level 0, so the pilot is not blocked — but a 7009A assessment that did could not be encoded at all. Recorded. | Same as A-07. Recorded now because the pilot's job is to find this before a real encoding hits it. |
| A-09 | `Development technical review` is a 7009B factor with no 7009A counterpart. Johnson has abundant technical-review content ([M&S 36] at p.10 and p.24) but never rates it as a credibility factor. | Populate `Factor Status` and the rationale from [M&S 36]; leave `Achieved Level` **blank**, listed. | A level Johnson never assessed is not derivable from evidence Johnson gathered for another purpose. Content is not a level. |

## Part 2 — package-level fields the source underdetermines

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| A-10 **ESCALATION** | `Standards Reference`. The paper applies **7009A**. The workbook's list offers `ASME-VV40-2018`, `NASA-STD-7009B`, `FDA-2023-CMS`, `Custom` — no 7009A. Worse, `excel_mapper.resolve_criteria_set` folds the version-agnostic alias `NASA-STD-7009` onto the **7009B** identifier: `resolve_criteria_set("NASA-STD-7009") -> https://uofa.net/criteria/NASA-STD-7009B`. A 7009A assessment entered the natural way is silently graded as 7009B. | Enter the literal string `NASA-STD-7009A`, which falls through to an author-namespace mint (`…/criteria/nasa-std-7009a`) rather than claiming the B identifier. Recorded as a tooling finding. | Never let a normalizer assert a version the source does not carry. An author-namespace identifier that is honest beats a project identifier that is wrong. |
| A-11 | `Decision Outcome`. The pack requires Accepted or Not accepted. The paper records **no acceptance decision**. Its closest sentence is "The results of this test and modeling effort are offered with the credibility level required for use of the results in the investigation's risk model" (p.10), followed by "(Signed)" with no name, no date, no deciding authority. | Leave `Decision Outcome`, `Decided By` and `Decision Date` **blank and listed**. Do not read "offered with the credibility level required" as an acceptance. | The modeller offering results is not the stakeholder accepting them. §3b: a cell is confirmed, corrected, or marked source-absent — an inferred decision is none of those. Note this is a *reporting* paper, so the absence is expected rather than a defect. |
| A-12 | `Model Risk Level` (MRL 1-5, V&V 40 Table 4-1). The paper has no MRL. It has a criticality assessment: "Single point failure in credible scenarios … Potential 1/300 probability of catastrophic failure … probable loss of aircraft with significant likelihood of pilot loss" (p.11). | Leave blank and listed. Record the criticality text in the COU description so the evidence is not lost. | An MRL is a V&V 40 construct assigned by a decision process. High consequence in prose is not an MRL, and inferring one would be the encoder grading the model. |
| A-13 | `Assurance Level` (Low / Medium / High). Not stated. | Blank, listed. | Same as A-12. |
| A-14 | `Device Class`. An FDA/domain-category field with no aerospace meaning here. | Blank, listed. | The field does not apply to the COU; leaving it blank is more honest than picking "Category A". |
| A-15 | `Has UQ?` at COU level. Not stated in those words, but the model delivers a quantified residual (0.0084 cm, p.9/p.22) and a "99% reliability/ 95% confidence tolerance bound 0.128 cm" (p.22). | `Yes`, anchored to p.22. | A value implied by an unambiguous quantitative statement is confirmable against the source. This is a confirmation, not an inference. |
| A-16 | `Assessor Name` / `Assessment Date`. The paper's assessment is the author's, and the report is undated internally; NTRS metadata carries 2020. | Assessor `K.L. Johnson (NASA NESC)` anchored to p.1; date left blank and listed rather than taken from NTRS metadata, which is outside the admissible inventory. | The evidence inventory fixed in SOURCE_SCOPING.md is the source. Catalogue metadata was not admitted, so it cannot be used now. |

## Part 3 — the source contradicts itself

These are not underdetermination. The source answers the same question two ways.
The outline's §5 trigger ("the source underdetermines a field") does not cover
them, which is itself the finding.

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| A-17 | **Waivers.** p.8 [M&S 32](7): "Validation using RWS or independent data not required per investigation team, approved by Technical Authority. **No waivers were required.**" One response both describes a TA-approved waiver and denies one. The p.23 caveats table answers the same requirement "None." | Encode **both readings** in the rationale, quoted, with both anchors, and mark the disposition JUDGMENT-CLASS. Do not pick. | Where a source states X and not-X, the encoding records the contradiction rather than selecting the reading that makes the package tidier. Choosing silently would make the encoder the author of the resolution. |
| A-18 | **Verification.** p.6: "Verification of the analysis code was waived since modeling required relatively straightforward multiple linear regression…". p.25 achieved rationale: "Analysis code in widely-used statistical software verified independently", rated 4 against a predeclared 3. | Record predeclared 3 and achieved 4 as the source states them, with both quotes in the rationale. Flag the tension; do not reconcile. | Same as A-17. The exceedance is real and is the paper's own claim; the encoder's job is to carry it with its context, not to explain it away. |
| A-19 | **[M&S 37] people qualifications.** p.10: "(Will not be covered in this report.)" p.24 answers it in full, with degrees and years of experience. | Use the p.24 content, anchored, and note the p.10 declination in the same cell's anchor. | Where one location declines and another answers, the answer is the evidence and the declination is context. This is the one contradiction with a defensible ordering rule, and saying why is what makes it a rule rather than a preference. |

---

## Appended during the extract-review pass

_Pending — the extraction has not run. See RUN_LOG.md for the blocking gate._
