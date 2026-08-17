# INV-17 — how often does a rule fire on an absence the judge says is present?

Status: **CLOSED** — the W-AR-05 case has siblings, and the chapter can carry a count
Date: 2026-08-17
Feeds: Ch4 boundary section, [INV-15 §4](INV-15-m5-scale-and-phase3-gap-probes.md), [INV-16](INV-16-nc-trajectory-decomposition.md)
Ruled: Addendum G.2 — *count it before the chapter uses it*

## The question

The results structure leans on the W-AR-05 case as **the** prose-invisibility example:
a rule fired because `comparedAgainst` was absent, while the judge wrote that
comparators exist. Both true, because the comparator lives in the prose.

If that is a single instance, the chapter must say so. If it recurs, the chapter gets
a measured pattern instead of an anecdote. **The answer is that it recurs, and
W-AR-05 is its most common member.**

## Headline

**Not a single instance.** Across **14,659 judgments** from three judges:

| | |
|---|---|
| Candidate sentences after filtering | **386** |
| Distinct cases | **332** |
| Hand-verified precision | **18 / 30 = 60.0%**, Wilson 95% CI [42.3%, 75.4%] |
| **Estimated genuine cases** | **≈ 199**, range **[141, 250]** |
| **W-AR-05 alone** | **104 cases**, 5 of 6 sampled genuine |

## Method, in three stages

**Stage 1 — the absence-checking set, defined from the catalog rather than by memory.**
Sixteen rules use `noValue` and therefore fire on the absence of a property. Those are
the only rules for which the pattern is possible.

**Stage 2 — mechanical shortlist.** For each judgment, sentences containing (a) a rule
id, (b) an assertion that the rule's *own subject* exists, and (c) that rule inside the
firing set the judge was shown (`reasoning_steps.rule_firings_inspected`). Requiring
the firing set is what makes it "the rule fired," not "the rule was mentioned."

**Stage 3 — corrections, all found by reading before counting.** The raw shortlist was
3,068 sentences; unfiltered it would have been a badly wrong number.

A first pass of this analysis reported 364/312 and a precision of 20/30. **It was
wrong in a way worth recording**: its disagreement regex was compiled with `re.X`,
which strips whitespace inside alternatives, so every multi-word marker — `does not
fit`, `false positive`, `not applicable` — silently never matched. Fixing it changed
the candidate set, which invalidated the hand-labelled sample drawn from the old one.
The 30 were re-drawn and re-classified against the corrected set. **A verified label
attached to the wrong sample is exactly the silent-null shape**, and it was caught
only because the committed script disagreed with the ad-hoc run.

### The methodological trap, recorded because it is the interesting part

**Six rules are *defined* as "X is present but Y is absent."** W-AL-02 is *"UQ present
but no documented sensitivity analysis."* W-CON-05 is *"activity present but no
evidence binding."* For these, a judge writing *"UQ is present"* is **restating the
rule's precondition, not contradicting it** — and a naive search counts every correct
firing as a disagreement.

W-AL-02 was the second-largest apparent contributor at 205 sentences. All of it was
artifact. **W-AL-02, W-CON-05, W-CON-04, W-SI-02, W-AR-02 and W-CON-01 are excluded
wholesale**, plus any sentence matching "present … but lacks/absent/missing" within
one sentence.

This is the same failure mode as the rest of the phase: a pattern-match that looks
like evidence until someone reads what it matched.

## Result, per rule

| Rule | its absent property | sentences | cases |
|---|---|---|---|
| **W-AR-05** | `comparedAgainst` | **107** | **104** |
| W-AL-01 | uncertainty quantification | 64 | 60 |
| W-EP-02 | generating activity | 53 | 52 |
| W-ON-02 | operating envelope | 50 | 48 |
| W-EP-01 | provenance chain | 47 | 47 |
| W-AR-01 | acceptance criteria | 30 | 29 |
| W-ON-01 | context of use | 19 | 19 |
| W-SI-01 | signature | 9 | 8 |
| W-PROV-01 | provenance chain | 6 | 6 |
| W-CON-02 | identifier resolution | 1 | 1 |

Representative, all hand-verified:

> **"W-AR-05 fired, yet comparator absence is not the central issue because a
> comparator exists in the narrative."** — judge A, and it needs no gloss at all
> "W-AR-01 was considered but rejected because acceptance criteria are present for the assessed factors."
> "Considered W-AL-01 (Missing Uncertainty Quantification) but rejected as UQ was present."
> "Considered W-ON-02 … but the package does contain a COU and operating envelope."
> "W-ON-01 covers missing context of use, but the package explicitly states the model
> purpose, device class context, patient population, operating envelope, and decision
> framing **in the description**."

Note the recurring giveaway — *"in the narrative"*, *"in the description"*,
*"comparisons are **described**"*. The judge is reading narrative; the rule is reading
the graph.

### A second finding inside the rejects

Of the 12 sampled rejects, one group is the judge simply agreeing with the firing. The
other is more interesting: **the judge asserts the rule's *precondition* is present and
calls the firing a false positive.** Three of the 30 say some version of *"W-ON-02 is a
false positive because a detailed ContextOfUse is provided"* — but a declared COU is
precisely what makes W-ON-02 eligible to fire; the rule reads the **envelope**. That is
a judge misreading which property the rule inspects, not a rule defect, and it argues
for the label-class partition from the opposite side: the LLM judge is unreliable
about *mechanical* questions of what a predicate reads.

## The inverse case, and it is the better quotation

Four judgments name the prose-versus-structure split outright **and side with the
rule**. These are rarer and stronger, because the disagreement cases require the
reader to trust the judge, while these require nothing:

> **W-ON-02, judge B**, quoting the package's own `hasContextOfUse.description` field:
> *"These ranges are described in the prose rationale but are not formally encoded as a
> machine-readable operating envelope or applicability constraint."* — the judge calls
> it *"a textbook example of the condition W-ON-02 is designed to detect."*

> **W-ON-01, judge A:** the package narrative *"explicitly says a structured Context of
> Use object has not been provided and that intended-use scope is described only in
> narrative text."*

**The corpus narrates its own gap.** A package written by one model, checked by a
deterministic rule, and read by another model, with all three agreeing that the
substance is in the prose and the structure is not there. That is the thesis stated
by the artifact rather than by the author.

## What the chapter can now say

**"One recorded instance" would be wrong.** The chapter can state that the
prose-versus-property split recurs across roughly 200 judgments, that W-AR-05 is its
most frequent single instance at 104 cases, and that it appears in every
absence-checking rule family measured — with the W-AR-05 case retained as the worked
example because it is the clearest.

State it with the interval and the skew, not as a bare number. The honest sentence is
*"recurs in the low hundreds of judgments"*, not *"199 times."*

## Coverage statement

**Measured.** All 14,659 judgment records across `judgments_A/B/C.jsonl` parsed. The
16 `noValue` rules extracted from `packs/core/rules/uofa_weakener.rules` by rule block.
Fields searched: `reasoning`, `alternative_rule_analysis`,
`reasoning_steps.instantiation_check`. Firing set taken per record from
`reasoning_steps.rule_firings_inspected`. Thirty candidates drawn at a fixed seed (3)
and classified by hand, one by one; the verdicts are inlined in
`studies/phase2_5a/count_prose_vs_property.py` so the precision figure is auditable
rather than asserted. Re-derive with
`python studies/phase2_5a/count_prose_vs_property.py`.

**Not measured.**
- **Precision rests on n=30.** The CI is wide [42.3%, 75.4%] and the point estimate of
  199 cases inherits that. It supports "low hundreds," not a specific figure.
- **Precision is not uniform across rules.** W-AR-05 scored 5/6 in the sample while the
  overall rate was 18/30, so the blended estimate understates W-AR-05 and overstates
  the weaker families. A per-rule precision estimate was not run — n per rule is too
  small in a 30-draw.
- **Judge A dominates: 302 of 386 sentences.** Judge A writes far longer
  `alternative_rule_analysis` text, so this measures *stated* reasoning, not
  underlying disagreement rates. **It is not evidence that judge A disagrees more.**
- **The firing set is the judge's own transcription**, not the analyzer's ground truth.
  A judge that mis-transcribed its firing list would be counted on its own error.
  Cross-checking against `outcomes.csv` per case was not done.
- **Sentence-level, not case-level.** A case is counted once per rule, but no attempt
  was made to adjudicate a case where one judge disagrees and another does not.
- **The four inverse cases were found by a narrow regex** requiring prose and
  structure vocabulary in one sentence. Judgments that make the same point across two
  sentences are not counted, so **four is a floor, not a total.**
