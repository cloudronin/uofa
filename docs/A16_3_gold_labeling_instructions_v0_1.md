# A16.3 Gold-Set Labeling Instructions v0.1

**Purpose:** produce the hand-labeled ground truth (100–150 cards) against
which judges calibrate and rules are scored. These instructions are part of
the pre-registration; they freeze with it and any mid-labeling amendment is
recorded as a dated change note, never silently.

**Labeler:** the author. **Blindness:** label from the card text only, never
with extractor or judge output visible for that card. If you recognize a
card whose assessment you have previously seen, label it anyway and mark
`seen_before=1` in the record; the analysis can hold those out.

---

## 1. The unit and the scope

- You label **one card at a time**, assigning each of the seven properties
  a value: `present`, `absent`, or `unclear`.
- **Card-level standard:** a property is `present` if the card's evaluation
  content states it for **at least one** reported result. Per-result
  granularity is adjudication territory (A16.4), not gold-set territory.
- **Section scoping is binding.** Only content under an evaluation-type
  heading (Evaluation, Benchmarks, Results, Performance, Testing, or an
  unambiguous equivalent) counts toward any property. Content elsewhere in
  the card, however relevant-sounding, does not. This rule exists because
  of a measured 11× error: 45% of cards mention a sampling temperature;
  only 4% state one for their evaluations. The rest is usage guidance.
- **The card is the artifact.** Content behind links (papers, eval reports,
  leaderboards) is NOT read and NOT counted. If the eval section says "see
  paper for details," the property the paper might contain is `absent` in
  the card; add `link_only=1` to the record so the study can report how
  often evidence is delegated rather than stated.
- **Sentinels are absence.** `N/A`, `-`, `none`, `not reported`, empty
  table cells, and equivalents mean `absent`, exactly as the adapters
  treat them. A field that names the property without carrying its content
  is absence wearing a label.

## 2. The seven properties

For each: what the claim IS, what counts, what does not.

<!-- BEGIN property-definitions -->
### P1. `score` — a reported benchmark score
- **The claim:** a numeric evaluation result reported for this model.
- **Present:** a benchmark name with a number attached, in prose or a table.
- **Absent:** a benchmark named with no result; a result for a different model only.
- P1 anchors the rest. If P1 is `absent`, P2-P7 are `absent` by construction.

### P2. `hasUncertaintyQuantification` — uncertainty attached to a reported score
- **The claim:** a quantified uncertainty attached to a reported result.
- **Present:** a stderr, CI, ±, variance across runs/seeds, or an explicit statistical qualifier attached to a reported result ("71.3 ± 0.4", "95% CI [69.9, 72.7]", "std across 3 seeds: 0.6").
- **Absent:** bare point scores; "results may vary" without a quantity; uncertainty stated for someone else's model in a comparison row but not for the subject model.

### P3. `samplingAccount` — how eval items relate to the claimed population
- **The claim:** how the benchmark items were drawn and how they relate to the population the score is read against.
- **Present:** "evaluated on the full test split"; "random 500-item subsample of X"; "items stratified by difficulty"; an explicit statement of subset selection and its rationale.
- **Absent:** merely naming the dataset ("evaluated on MMLU"); item counts with no account of selection ("1,500 questions"); dataset citations.
- Naming which items came from where is not an account of how they relate to the target population - the exact distinction that voided the `provenance.sampling` claim.

### P4. `harnessDeterminismStatement` — the conditions the scores were produced under
- **The claim:** the decoding and run conditions under which the reported numbers were produced.
- **Present:** decoding/eval settings stated FOR the evaluation (temperature, seed, greedy decoding, n-shot regime with sampling config, repeat-run policy): "all evals at temperature 0, 5-shot", "3 runs, greedy".
- **Absent:** inference recommendations for users ("we suggest temperature 0.6 for thinking mode") anywhere in the card, including when they appear near eval content; harness version alone with no settings.
- **Does NOT count:** An n-shot value alone is a PROMPT REGIME, not a measurement policy. `n-shot=0, filter=none` in an lm-eval-harness table states how the prompt was built and is silent on repeats, seeds and decoding - it is `absent`. The present-example's "with sampling config" is load-bearing (CLASS-LMEVAL-P4, upheld 2026-08-11).

### P5. `nullBaselineStatement` — a chance/null/comprehension-free reference
- **The claim:** an explicit chance or null reference for a reported result.
- **Present:** an explicit chance or null baseline for at least one reported result ("random baseline: 25%", "majority-class: 51%", "chance level shown in table"); an explicit statement that scores are normalized or calibrated against chance/null performance ("the scores for each task are normalised to account for baseline performance due to random chance") -- a CALIBRATION claim, which satisfies the property even where no chance value is printed, because the null sits at a known reference point on the normalized scale by construction.
- **Absent:** comparisons to other models only (a rival model is a comparator, not a null); "significantly above chance" with no stated chance value MAY be `unclear` - see §3.
- **Does NOT count:** A COMPARATIVE claim is not a calibration claim, and only the second satisfies P5. "+66% vs Random Baseline", "beyond random baseline", "significantly above chance" all assert performance RELATIVE TO an unstated null: they give the gap and never the null, so a reader cannot recover the reference. "Scores are normalised to account for baseline performance due to random chance" asserts the scoring METHODOLOGY incorporates the null. Different constructs. The test is whether the null is recoverable, not whether a number is printed.

### P6. `claimedCOU` — a stated context of use for the evidence
- **The claim:** what decision or deployment context the reported evaluation is meant to inform.
- **Present:** "these results support use for X / are intended to demonstrate fitness for Y"; an eval section explicitly tied to an intended-use statement ("we evaluate on medical QA to assess suitability for clinical information retrieval").
- **Absent:** a generic intended-use section elsewhere in the card that the eval content never connects to; benchmark scores presented without any statement of what they are evidence FOR.
- The connection must be stated, not inferable.
- **Does NOT count:** A model-level use disclaimer is NOT a claimed COU, however emphatic, and however close to the eval text it sits: "provided for research and development purposes only", "Research use only", "not intended to inform decisions central to human life", "the primary intended users are AI researchers". Each states a boundary on the MODEL with no eval result attached. Naming an audience is likewise absent. A negative COU DOES count when the evaluation is what leads to it ("...render the current model unsuitable for deployment in practical medical applications") - the test is the stated connection, not the polarity.

### P7. `confoundControlStatement` — capability confound addressed
- **The claim:** the card addresses whether a measured separation reflects the measured construct rather than general capability.
- **Present:** capability-matched comparisons; partialling; ablations offered as controls; an explicit limitation statement doing this work ("gains persist after controlling for model size").
- **Absent:** raw cross-model comparisons; bigger-model-wins tables; generic limitations boilerplate that does not touch the confound.
- **Does NOT count:** Declaring MEMBERSHIP in an ablation is not offering one as a control. "This repository contains the evaluation results of the base model... as part of an ablation study", with only this arm's numbers and no comparison, is `absent`. The present-example requires the ablation do the confound work IN THIS CARD - as in "we compare with an ablation model that does not use transliteration" or a LoRA rank chosen "to match trainable params".
<!-- END property-definitions -->

## 3. `unclear`, and how to use it

- `unclear` is for genuine ambiguity of the CLAIM (e.g. "significantly
  above chance", a ± whose meaning is never defined), not for labeling
  fatigue. Every `unclear` carries a one-line note.
- Budget expectation: if `unclear` exceeds ~10% of labels on a property,
  stop and amend the instruction (dated change note) rather than absorbing
  drift — the ambiguity is the instruction's fault, not yours.
- `unclear` cards are excluded from judge-calibration scoring for that
  property and routed to A16.4 adjudication; they still count in
  prevalence reporting as their own category.

## 4. Record format

One row per card, CSV, committed to `studies/taxonomy-validation/gold/`:

```
card_id, row_hash, task_category, seen_before, link_only,
P1..P7 ∈ {present, absent, unclear},
P1..P7_note (free text, required for unclear, encouraged for edge calls),
session_id, labeled_at
```

- `row_hash` is the Liang-parquet row content hash (the A9.1 artifact pin);
  it is what makes the gold set re-derivable against the frozen corpus.
- Label from the parquet's card content, not from live HF — the study's
  population is the snapshot.

## 5. Session mechanics

- **Calibration first:** label 10 cards, then re-label the same 10 at the
  next session's start before seeing your originals. Self-agreement below
  ~90% on any property means the instruction for that property gets
  tightened before proceeding. Cheap insurance on 150 cards' worth of
  signal.
- Work in sessions of 20–30 cards; note `session_id` so order effects are
  checkable. Expect early cards to be slow (5–8 min) and later ones fast
  (2–3 min); do not let speed relax the section-scoping rule, which is the
  one discipline fatigue attacks first.
- When a card presents a genuinely new edge case, stop, decide, record the
  decision as a dated note appended to this file, and apply it forward.
  Do not retro-fit earlier labels mid-study; a final consistency pass at
  the end applies all accumulated notes once, as its own recorded step.

## 6. What this gold set is not

It is not a judgment of any model, author, or card quality. Every label is
a statement about what the card's evaluation content states, under the
scoping rules above — the same scope sentence the report card carries,
applied at the level of a single property.
