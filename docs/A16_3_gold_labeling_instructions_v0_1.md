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

### P1. `score` — a reported quantitative result
- **Present:** at least one benchmark result with a numeric value under an
  eval heading (table or prose: "MMLU: 78.2").
- **Absent:** qualitative claims only ("strong performance on reasoning"),
  or numbers only outside eval scope.
- Note: P1 anchors the rest. If P1 is `absent`, P2–P7 are `absent` by
  construction (there is no evaluation evidence to have properties), but
  still record them explicitly — do not leave blanks.

### P2. `uncertaintyStatement` — uncertainty attached to a reported score
- **Present:** a stderr, CI, ±, variance across runs/seeds, or an explicit
  statistical qualifier attached to a reported result ("71.3 ± 0.4",
  "95% CI [69.9, 72.7]", "std across 3 seeds: 0.6").
- **Absent:** bare point scores; "results may vary" without a quantity;
  uncertainty stated for someone else's model in a comparison row but not
  for the subject model.

### P3. `samplingAccount` — how eval items relate to the claimed population
- **The claim:** how the benchmark items were drawn and how they relate to
  the population the score is read against.
- **Present:** statements like "evaluated on the full test split",
  "random 500-item subsample of X", "items stratified by difficulty",
  or an explicit statement of subset selection and its rationale.
- **Absent:** merely naming the dataset ("evaluated on MMLU"), item counts
  with no account of selection ("1,500 questions"), dataset citations.
  Naming which items came from where is not an account of how they relate
  to the target population — this is the exact distinction that voided the
  `provenance.sampling` claim.

### P4. `harnessDeterminismStatement` — the conditions the scores were produced under
- **Present:** decoding/eval settings stated FOR the evaluation
  (temperature, seed, greedy decoding, n-shot regime with sampling config,
  repeat-run policy): "all evals at temperature 0, 5-shot",
  "3 runs, greedy".
- **Absent:** inference recommendations for users ("we suggest
  temperature 0.6 for thinking mode") anywhere in the card, including
  when they appear near eval content; harness version alone with no
  settings.

### P5. `nullBaselineStatement` — a chance/null/comprehension-free reference
- **Present:** an explicit chance or null baseline for at least one
  reported result ("random baseline: 25%", "majority-class: 51%",
  "chance level shown in table").
- **Absent:** comparisons to other models only (a rival model is a
  comparator, not a null); "significantly above chance" with no stated
  chance value MAY be `unclear` — see §3.

### P6. `claimedCOU` — a stated context of use for the evidence
- **The claim:** what decision or deployment context the reported
  evaluation is meant to inform.
- **Present:** "these results support use for X / are intended to
  demonstrate fitness for Y", or an eval section explicitly tied to an
  intended-use statement ("we evaluate on medical QA to assess suitability
  for clinical information retrieval").
- **Absent:** a generic intended-use section elsewhere in the card that
  the eval content never connects to; benchmark scores presented without
  any statement of what they are evidence FOR. The connection must be
  stated, not inferable.

### P7. `confoundControlStatement` — capability confound addressed
- **The claim:** the card addresses whether a measured separation reflects
  the measured construct rather than general capability.
- **Present:** capability-matched comparisons, partialling, ablations
  offered as controls, or an explicit limitation statement doing this work
  ("gains persist after controlling for model size").
- **Absent:** raw cross-model comparisons; bigger-model-wins tables;
  generic limitations boilerplate that does not touch the confound.

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
