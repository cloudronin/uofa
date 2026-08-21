# Ambiguity log — Johnson encoding pilot

State: **RE-ADJUDICATED by the author, 2026-08-21.** The entries below are the
DRAFT resolutions this session chose; they are left as written, because they are
the record of what the draft decided. The author's verdict on each is in the
**Re-adjudication** section at the end of this file, and that section is the
authority. The record's four mis-addressed rulings were escalated rather than
reconciled, and the author re-issued them by subject on 2026-08-21; the
re-adjudication table carries the re-issued form. `APPLY_RECORD_ESCALATIONS.md`
holds the round-trip. **All 30 entries are adjudicated. Nothing in this log is
awaiting the author.**

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

Entries A-20 onward were raised during the extract-review pass and the import.

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| A-20 | Anchor granularity. Spec §2.1 says *every populated cell* carries an anchor. A spreadsheet's natural unit is the row, and a row often cites several pages. | Workbook carries one `Source Anchor` per **row**; per-**cell** anchors live in `REVIEW_LEDGER.md`, which records the anchor beside the extractor value and the reviewed value for each of the 97 decisions. | Where the required granularity does not fit the artifact, record it at the artifact's granularity and keep the finer record beside it rather than degrading it. Both are committed, so nothing is lost. Filed as a §2b finding. |
| A-21 | `Compares To` on Validation Results expects a URI. Three of the five comparators are not entities a URI names: SME engineering judgment, a review panel, and "RWS data (not available)". | Left the prose the extractor wrote. Import logs them as non-well-formed subjects and drops them, which is why W-AR-05 fires five times (D-02 to D-06). | Do not mint an identifier for a comparator the source describes but does not identify. A fabricated URI would satisfy the rule and misrepresent the source. |
| A-22 | Factor status for the V&V 40 factors carrying evidence but no level. `assessed` implies a level; `not-assessed` denies the evidence. | `assessed` for the four the LCW answers directly (Numerical code verification, Model form, Output comparison, and `scoped-out` for Numerical solver error), `not-assessed` for the rest. | Status describes whether the source addressed the factor, not whether a level exists. Consequence accepted: the three `assessed`-without-level factors each draw W-CON-01 (D-07 to D-09). |
| A-23 | `Discretization error` status. Extractor said `not-assessed`; the factor is meaningless for a regression on test data. | `not-applicable`. | `not-assessed` says nobody looked; `not-applicable` says there is nothing to look at. A linear regression has no discretization scheme. |
| A-24 | Whether the review pass may **add** rows the extractor never emitted — specifically a `ProcessAttestation` for the process evidence at p.25, which would clear W-NASA-03 (D-10). | **Not resolved. No row added.** The pass corrected and blanked what the extractor emitted and did not author new evidence entities. | Spec §2 describes review as confirm / correct / mark source-absent, three verbs that all act on an existing cell. Adding an entity is a fourth act the protocol does not define. Escalated as F-5 rather than decided. |
| A-25 | Package base URI. Import warns that identifiers are minted under `https://example.org`, a placeholder. | Left as the placeholder, warning recorded. | Nothing is signed, so no identifier is frozen; asserting a namespace for a DRAFT would be a claim the pilot has no basis to make. The on-ramp page never mentions `base_uri`, which is itself a §1 finding. |

Entries A-26 onward were raised during the governed-pass prep, under the protocol draft.

| ID | Ambiguity | DRAFT resolution | Rule applied |
|---|---|---|---|
| A-26 | Cross-reference identifiers. `comparedAgainst` and `hasEvidence` are `@type: @id` terms in the v0.5 context, so a relative value is dropped at JSON-LD expansion and the reference never reaches the graph, without warning. An absolute IRI requires knowing the minting namespace, which is an author decision not frozen until signing. | `review_pass.py` carries `BASE_URI` as a single constant and mints every cross-reference from it, so changing the namespace is one edit plus a re-run. | Where a workbook value must encode a decision the workbook cannot see, keep the decision in one named place rather than spread through cells. Filed as a template finding: the workbook needs a namespace-relative identifier form. |
| A-27 | `base_uri` choice. §1f requires a namespace the encoder controls. `https://uofa.net` is refused by `resolve_base_uri` as reserved for the project's published examples. | `https://github.com/cloudronin/uofa`, the author-controlled repository namespace. **AUTHOR-CONFIRM before signing**, because the id is covered by the signature and cannot change afterward. | Use a namespace demonstrably controlled by the author and visible in the repo's own remote rather than inventing one. Supersedes A-25, which recorded the placeholder as a deviation. |
| A-28 | W-AR-05 fires on evidence types that have no comparator. `ReviewActivity`, `ProcessAttestation`, and `DeploymentRecord` all ride `hasValidationResult`, and the pattern tests every node under it. | Dispositioned **Not Applicable** on the three affected nodes rather than Accepted, and the mis-scoping filed as a rule finding. | A pattern reporting an absence that could never be a presence for a node class is not describing a gap in the encoding. Established by controlled experiment: the `ProcessAttestation` added under §3c drew the firing immediately. |

Entries A-29 and A-30 were opened on 2026-08-21, in the author's governed review pass.
Both record a disclosure the source makes about its own evidence, which the earlier
passes carried in the encoding without logging as an ambiguity. They are the two
source-disclosure entries the E-2 escalation identified as missing.

| ID | Ambiguity | Resolution | Rule applied |
|---|---|---|---|
| A-29 | **Incomplete randomization.** The test program's randomization was not fully executed, and the source records SMEs judging the shortfall inconsequential. Whose judgment does the encoding record — the SMEs' or the encoder's? | Record the incompleteness and the SME judgment **as the source's**, quoted and anchored. The encoding does not endorse the judgment and does not restate it as a finding of its own. | An assessment's own disclosure of a limitation is evidence about the assessment, and carrying it is not agreeing with it. Where the source judges its own shortfall, the encoding records who judged. Author ruling 2026-08-21. |
| A-30 | **Retained outlier.** The source discloses retaining an outlier, "pulling it less than 0.003 cm in nonconservative direction". A disclosed nonconservative adjustment invites an encoder verdict on whether retention was sound. | Record the disclosure, quoted and anchored. **No encoder ruling on the retention.** | Same rule as A-29, in its sharper form: the encoder has no standing to adjudicate a modelling decision the source discloses and defends. Recording it without ruling on it is the honest act. Author ruling 2026-08-21. |

**Anchors for A-29 and A-30 — CONFIRMED 2026-08-21.** The dispositions round-trip gave
p.24 for both; the committed anchors in `PROTOCOL_FINDINGS.md` F-4d are p.8, p.15 and
p.23 for the randomization and p.21 for the outlier. F-4d's anchors govern and are the
ones used above. Ruled on the same principle as everything else in this pass: the
anchored record outranks a conversational summary of it.

---

# Re-adjudication by the author — 2026-08-21

Source: `Johnson_Author_Verdict_Record.md`, sections "Step 1", "Step 2", "Dispositions",
"Silence sweep" and "Ambiguity log". Applied mechanically; nothing here is this session's
judgment.

The record accounted for 28 entries as **22 auto-resolved** and **6 individually ruled**.
Two of the six (A-10, A-26) matched the entry the record named and were applied on the
first pass. The other four did not, were escalated as E-1, and were **re-issued by subject
by the author on 2026-08-21**. The re-issued form is what this table carries:

- The **waivers self-contradiction** is log entry **A-17**, and its ruling is the entry's
  own rule — *do not pick*. The record's summary had imported answer-outranks-declination,
  which is A-19's rule; that import is withdrawn. Protocol A-9 states the ordering rule
  covers one of this source's three contradictions, and this is one of the other two.
- The **negotiated Use history predeclaration** is not a log entry. It is F-4d's worked
  candidate, and the author's confirmation lands in the disposition and finding record
  rather than here.
- **Incomplete randomization** and the **retained outlier** are now entries A-29 and A-30,
  opened under E-2.
- The entries the record's four rulings displaced — **A-13, A-19 and A-22** — had never
  actually been reviewed. They were returned to the author, quoted one line each, and
  **all three were confirmed as drafted on 2026-08-21**. A-19 was ruled first, because it
  is where answer-outranks-declination properly lives and ruling it accounts for the
  import withdrawn from A-17.

| ID | Subject | Author verdict, 2026-08-21 | Route |
|---|---|---|---|
| A-01 | Uncertainty Characterization → `Results uncertainty` | Re-adjudicated, CONFIRMED | Step 2 item 1 — row 21 levels confirmed against Table 3 and p.25 |
| A-02 | M&S History → `Use history` | Re-adjudicated, CONFIRMED | Step 2 item 1 — row 23 levels confirmed. *The record's "A-17 negotiated predeclaration (Use history)" is F-4d's worked candidate, not this entry; the author's confirmation of it lands in the disposition and finding record — E-1* |
| A-03 | M&S Process / Product Management → `Development process and product management` | Re-adjudicated, CONFIRMED | Step 2 item 1 — row 20, including the required 2 / achieved 4 exceedance |
| A-04 | Verification: do not fan out the level | Re-adjudicated, CONFIRMED | Silence sweep — declined mappings and scale-boundary declinations, confirmed as tabled |
| A-05 | Validation: do not fan out the level | Re-adjudicated, CONFIRMED | As A-04 |
| A-06 | The 0-4 / 1-5 scale boundary | Re-adjudicated, CONFIRMED | Silence sweep — the scale-boundary declinations |
| A-07 **ESCALATION** | `Input pedigree` has no factor in the pack | **ACKNOWLEDGED as the record. Stands unresolved.** | Silence sweep — one of the two escalations, no disposition possible. INV-20 channel |
| A-08 **ESCALATION** | Level 0 inexpressible on 13 of 19 factors | **ACKNOWLEDGED as the record. Stands unresolved.** | Not triggered by this source; filed against the next one |
| A-09 | `Development technical review` has no 7009A counterpart | Re-adjudicated, CONFIRMED | Silence sweep — Source-absent level; content at p.10 / p.24 is not a level |
| A-10 **ESCALATION** | `Standards Reference`: the 7009A / 7009B dual standard | **Individually ruled: ACKNOWLEDGED, stands.** | Also Step 2 item 3 — the `NASA-STD-7009A` literal confirmed in Assessment Summary |
| A-11 | `Decision Outcome`, `Decided By`, `Decision Date` | Re-adjudicated, CONFIRMED | Step 2 item 2 — outcome Accepted anchored p.19; Decided By and Decision Date remain blank as faithful to source |
| A-12 | `Model Risk Level` | Re-adjudicated, CONFIRMED | Step 2 cell walk — blank-and-listed |
| A-13 | `Assurance Level` (Low / Medium / High). Not stated. | **CONFIRMED as drafted, 2026-08-21.** Blank and listed is the only honest resolution: assigning an assurance level the source never states would be the encoder grading the model, which is what A-12's rule exists to prevent. Same family as the Decision-cell blanks ruled at Step 2 item 2 | E-1, resolved |
| A-14 | `Device Class` | Re-adjudicated, CONFIRMED | Step 2 cell walk — blank-and-listed |
| A-15 | `Has UQ?` at COU level | Re-adjudicated, CONFIRMED | Step 2 cell walk — confirmed Yes, anchored p.22 |
| A-16 | `Assessor Name` / `Assessment Date` | Re-adjudicated, CONFIRMED | Step 2 cell walk |
| A-17 | **Waivers.** p.8 describes a TA-approved waiver and denies one; p.23 answers "None" | **CONFIRMED**, ruling re-issued by subject 2026-08-21. **No harmonization.** The entry's own do-not-pick rule governs, not answer-outranks-declination; that import is withdrawn as an error of the record's summary. Both anchors retained. The encoding carries the specific waiver record as data; the contradiction stays open in the log | E-1, re-issued |
| A-18 | **Verification.** waived at p.6, rated 4 against a predeclared 3 at p.25 | Re-adjudicated, CONFIRMED | Silence sweep — the scale-boundary declination; the exceedance is carried with both quotes and not reconciled |
| A-19 | **[M&S 37] people qualifications.** declined at p.10, answered at p.24 | **CONFIRMED as drafted, 2026-08-21.** Ruled first of the three, deliberately: this is the legitimate home of *answer outranks declination*. p.10 declines to cover qualifications, p.24 answers in full, the specific answer wins, and the declination is kept in the same cell's anchor as context. Confirming it here closes the loop on the withdrawn A-17 import — the rule now lives on the entry it belongs to and nowhere else | E-1, resolved |
| A-20 | Anchor granularity: row-level in the workbook, cell-level in the ledger | Re-adjudicated, CONFIRMED | Step 2 cell walk; the §2b finding stands |
| A-21 | `Compares To` expects a URI; three comparators are not URI-shaped | Re-adjudicated, CONFIRMED | D-02 and D-06; cited as the SF-2 instance |
| A-22 | Factor status for evidence-without-level factors: `assessed` implies a level, `not-assessed` denies the evidence | **CONFIRMED as resolved, 2026-08-21.** The status split stands: `assessed` for the four factors the LCW answers directly, `scoped-out` for Numerical solver error, `not-assessed` for the rest — which is what the Step 2 cell walk verified. **Kept on the record:** D-07 to D-09 are Confirmed as the accepted *consequence* of this resolution and are not an adjudication of it. This ruling is the adjudication | E-1, resolved |
| A-23 | `Discretization error` status | Re-adjudicated, CONFIRMED | Step 2 item 5 — `not-applicable` confirmed |
| A-24 | May the review pass **add** rows? | **CLOSED.** Resolved by §3c; the `ProcessAttestation` row is confirmed as warranted | Step 2 item 6, with the dual-anchor correction applied to the row and the ledger |
| A-25 | Package base URI placeholder | Re-adjudicated, CONFIRMED as superseded by A-27 | Step 1 |
| A-26 | Cross-reference identifiers: relative IRIs silently dropped at expansion | **Individually ruled: ACKNOWLEDGED as an ESCALATION-class tooling finding.** Stands in the tooling channel | Step 1 / findings |
| A-27 | `base_uri` choice, `https://github.com/cloudronin/uofa` | **RULED: keep as minted. Resolves as CONFIRMED-BY-AUTHOR.** The AUTHOR-CONFIRM gate on this entry is discharged | Step 1 |
| A-28 | W-AR-05 fires on evidence types that have no comparator | Re-adjudicated, CONFIRMED | D-03 to D-05, now verdict-backed including the controlled experiment; SF-1 |

| A-29 | Incomplete randomization, and whose judgment the encoding records | **RULED 2026-08-21.** Recorded as the source's SME judgment, not encoder endorsement | Opened under E-2 |
| A-30 | Retained outlier, disclosed as nonconservative by less than 0.003 cm | **RULED 2026-08-21.** Disclosure recorded without encoder ruling | Opened under E-2 |

**Reconciliation of counts.** **30 entries, all adjudicated.** The record's 28 was the
pre-walk state; A-29 and A-30 were opened and ruled on 2026-08-21 under E-2. Of the 30:
25 re-adjudicated from the record, 2 opened and ruled in the same pass, and 3 (A-13, A-19,
A-22) returned to the author on the E-1 escalation and confirmed as drafted. A-07 and A-08
are within the adjudicated group, carried as acknowledged escalations rather than resolved —
an acknowledgement is the verdict, not a resolution. **Nothing in this log was adjudicated
by the apply-record session**; every verdict above is the author's.
