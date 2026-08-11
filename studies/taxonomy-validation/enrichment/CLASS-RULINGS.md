# Class rulings on the enrichment draft

**Applied 2026-08-11**, covering 62 rows. Each is ruled **against the standard
the gold set already set**, not freshly. The two strata must be labeled to one
bar: sensitivity is measured on the gold set and specificity on this one, and a
different standard on each measures the two against different definitions of the
property.

Labels remain `claude-assisted-draft-NOT-GOLD-until-human-confirmed`. These
rulings make the draft self-consistent; they do not confirm it.

---

## The anchors these rulings are made against

Committed gold positives, with the labeler's own notes:

**P3_sampling** — all three are *population-relationship* accounts, none is a
sample size:

| Card | Note |
|---|---|
| `projecte-aina/bart-base-ca-casum` | "an out of distribution test set, VilaSum" |
| `lmqg/t5-base-subjqa-tripadvisor` | "Out-of-domain Metrics section = explicit in/out-of-domain distinction" |
| `mbeukman/xlm-roberta-…-amharic` | "data distribution similar to training set… do not directly indicate how well these models generalise" |

**P4_determinism** — all three state *conditions under which the number was
produced*:

| Card | Note |
|---|---|
| `fxmarty/20220711-…-conll2003` | "3s/config, batch=1, len=64 (time metrics only)" |
| `DMetaSoul/sbert-chinese-qmc-domain-v1` | "10K samples, V100, batch_size=16, max_seq_len=256" |
| `mbeukman/xlm-roberta-…-amharic` | "seed was chosen that gave the best overall F1 = selection procedure stated" |

---

## CLASS-SEALION (13 rows) → P3 **absent**

> "The evaluation was done zero-shot with native prompts on **a sample of
> 100-1000 instances for each dataset**."

A sample **size**, silent on how instances were drawn or how they relate to the
target population. Every gold P3 positive is a population-relationship claim;
none is a count. Ruling it present would admit a category the gold set excluded
and make P3 mean something different in each stratum.

Not `unclear` either — the card is not ambiguous. It states a size and says
nothing about the relationship. That is an absence, and absences are the labels
that carry information here.

**P5 is unaffected and stays `present`** for this family, on the separate
sentence "the scores for each task is normalised to account for baseline
performance due to random chance." That is a genuine chance-normalization
statement and it is the anchor for 13 of the 22 P5 positives.

## CLASS-STEFANIT (10 rows) → P4 **present**

Five-run tables reporting `0.5409 ± 0.0222` across five linked run results.

The gold anchor accepted "seed was chosen that gave the best overall F1" as
present, on the grounds that it discloses the selection procedure. A five-run
mean±std discloses strictly more: it shows every run and aggregates rather than
selecting. Ruling this absent while that is present would invert the standard.

**P2 is separately `present`** on the same tables — the `±` is a real dispersion
over five runs, not a tolerance band. These are the strongest P2 positives in the
stratum precisely because the runs are individually linked.

## CLASS-LMEVAL-P4 (8 rows) → P4 **absent** — the marginal one

lm-eval-harness output tables carrying `n-shot` and `filter` columns.

Ruled absent, and this is the ruling most worth a second opinion.

**For present:** the gold anchor `fxmarty` accepted harness-emitted conditions
(3s/config, batch=1, len=64), so harness provenance alone does not disqualify.

**For absent, which won:** P4 is *determinism*. `fxmarty`'s conditions determine
the measured value — a timing number is meaningless without batch and length.
`n-shot` is a task setting; it says nothing about run repetition, seeds, or
decoding temperature, which is what the property is about. The card states how
the prompt was built and stays silent on whether the number would reproduce.

Labeling records what the card says, so the tiebreak is not which error is safer
but which reading is accurate. **If this is overturned, 8 rows flip and nothing
else changes** — the ruling is isolated by design.

## CLASS-NVIDIA-P6 (3 rows) → P6 **absent**

> `| Intended Users: | Research |`

A structured model-level metadata row in NVIDIA's card template — the same
category as the HuggingFace template's `## Intended uses & limitations`, which
this pipeline's own pre-filter excluded **1,884 times** in the field arm as
template furniture.

Ruling it present would have the search filter and the labeling standard
disagree about the same phenomenon in the same run. It also fails P6 on its
merits: it names an audience, not a claim about what the evaluation supports.

## CLASS-TEMPLATE-EMPTY (28 rows) → all **absent**

Auto-generated Qwen/Gemma stub cards with an evaluation heading and no content.
Confirmed as drafted. They are the stratum's trivial negatives and they belong in
it — §5.2 keeps negatives.

## CLASS-MRFT (3 rows) — no ruling needed

Already labeled, and already the strongest false-positive keepers in the set:
`Within ±1 Level` is a tolerance band (P2 absent) and `ablation` appears only as
a repo/script name (P7 absent). Both carry `hard_assert` in
`tests/fixtures/specificity/cases.json` because both are facts about the text
rather than judgments about the card.
