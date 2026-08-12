# A keyless route for table-borne evidence

> **IN-SAMPLE DEVELOPMENT RECORD — not a qualification result.**
> The route was developed, diagnosed and repaired against the same cases it
> scores on: the eight lm-eval header misses were found on these cases and fixed
> for these cases. That is training on the test set. The LLM rows do NOT share
> the defect -- prompt v2 renders from the sheet and was never tuned against case
> outcomes -- so the comparison below is **asymmetric in the route's favour**.
> Nothing here may enter the qualification table or wire into `card_prose` until
> the holdout gate runs (`KEYLESS-HOLDOUT.md`).

**Measured 2026-08-12.** Prompted by the observation that `keyless_extractor.py`'s
pattern may apply to Group B. It does, on exactly one cell, and the numbers say so.

## The result

Table-borne P2 uncertainty, 116-case stratum, corrected labels:

| Extractor | false-fire | false-clear | cost |
|---|---:|---:|---|
| **keyless route** *(in-sample)* | **0/25 (0%)** | 0/8 (0%) | none |
| `Llama-3.3-70B` (v2) | 2/25 (8%) | 0/8 (0%) | API |
| `DeepSeek-V4-Pro` (v2) | 12/25 (48%) | 0/8 (0%) | API |

**Zero misses on 25 cases, no model, no key, no tokens, fully deterministic** --
**in sample**. Whether it clears the bar is what the holdout gate decides; this
number cannot answer that, because the route was repaired against these cases.

On prose it **declines**: 0% false-clear, 89% false-fire. That is the
`_blank` contract working as designed — it reads what it can read and stays
silent otherwise, rather than guessing and satisfying a `minCount` with a
plausible value.

## Why it works, and why the first attempt did not

The first route required the dispersion token and its number on the **same
line**. It scored 33% — worse than the LLM. All eight misses were one shape:

    |    Task     |Version| Metric |Value |   |Stderr|
    |arc_challenge|      0|acc     |0.5401|±  |0.0146|

lm-eval-harness puts `Stderr` in a **header** and its values in data rows. A
line-regex cannot see that; the word and the value are rows apart. The working
route parses the table: find a header cell naming a dispersion, then read a
number from that column in any data row.

That is a **field read**, which is what makes it legitimate under D2 —
"structured input reads deterministically, prose requires a backend". A markdown
eval table is structured input. Reading `0.0146` out of a `Stderr` column infers
nothing, and the LLM's near-perfect 8% on the same cell was the signature of a
task that never needed a model.

## The false-clear was a label error, now adjudicated and corrected

Author-confirmed 2026-08-12: the row flips to `present`, so table-borne P2 is now
25 positives and the route's false-clear denominator is 8, at 0%.

**Both LLMs' P2 false-clear also drops 11% -> 0%.** Their single apparent
invention was this same mislabeled card; neither model ever fabricated a P2
uncertainty. They had been penalized for a label error.

The adjudication basis was the card text against the sheet clause, quoted -- not
the route's disagreement. A tool may surface a candidate label error; labels
change only by clause-cited adjudication.

### Original note (retained)

`ibraheemmoosa/xlmindic-base-uniscript-soham`, labeled P2 `absent` with **no
reason recorded**:

> `Wikipedia Section Title Prediction | 71.90 | 65.45 | 69.40 | **81.78 ± 0.60** | 77.17 ± 0.76`

`81.78 ± 0.60` on the bolded subject column is a textbook Present under the
sheet. Its sibling card states "the mean and standard deviation of nine
fine-tuning runs". So the route's true false-clear on this cell is plausibly 0/1.

**Not flipped here.** Correcting a label because a route disagrees with it, mid
-measurement, is the move this study exists to avoid. It goes to the same review
queue as the P5 rows.

## What this changes architecturally

The extraction question stops being *"which model can read all four
properties"* and becomes **routing by evidence structure**:

| Evidence | Route | Status |
|---|---|---|
| table-borne (P2, some P5) | **keyless field read** | 0/25 in-sample; **holdout gate pending** |
| prose-borne lexical (P2, P5) | LLM extraction | 44–100% miss, unresolved |
| prose-borne relational (P6, P7) | **panel** | pre-committed in A16.4 |

Three consequences worth stating:

1. **Most P2 evidence is table-borne** — 25 of 34 positives. So the property with
   the largest positive class *may* be largely solved by a route that costs
   nothing, pending the holdout gate.
2. **It is reproducible in a way an LLM row is not.** No temperature, no seed, no
   `prompt_sha256`, no provider availability. The pin is the code.
3. **It does not touch P6/P7 at all.** Both have zero table-borne positives, so
   this route is silent on them by construction — which is the honest blank, and
   the reason A16.4's panel routing was pre-committed independently.

## What has NOT been done

- **Not shipped.** This is a prototype measured on the stratum, not wired into
  `card_prose` or the report path.
- **Not a full row.** It covers P2 table-borne. A P5 chance-value column route is
  authorized as an extension behind the same holdout gate; no property enters the
  keyless route on in-sample evidence alone.
- **Not measured against a null model.** `keyless_extractor.py`'s contract is that
  every confidence is what the route scored against reading nothing. On this
  stratum a null model scores 100% false-fire by construction, so the comparison
  is trivial — but a real route in the shipped path needs the corpus-scale
  version of that check before it carries a confidence number.
