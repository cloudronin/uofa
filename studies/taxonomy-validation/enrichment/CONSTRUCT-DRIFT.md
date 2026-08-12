# Construct drift between the labeling sheet and the extraction prompt

**Checked 2026-08-11.** Step 1 of the three-step order set before authorizing any
prompt redesign.

## Why this check came first

Three unrelated model families — Qwen, Meta, DeepSeek — independently read the
same 20 P6/P7 cards as silent. That is evidence about *something*, but it points
at extractor capability **only if the labels and the prompt define the same
property**. If they do not, the measurement compared two constructs, and
redesigning the prompt would have optimized the extractor toward the labeler's
reading rather than toward the property.

The check is mechanical and cost nothing: put the instruction sheet's definition
beside the prompt's field description and read them.

**They drifted.** On three of four enriched properties, and in the direction that
produces exactly the failures observed.

## The comparison

Sources: `docs/A16_3_gold_labeling_instructions_v0_1.md` §2 and
`packs/mrm-nist/prompts/card_eval_extract_prompt.txt`.

| | Instruction sheet — PRESENT | Extraction prompt — field description | Drift |
|---|---|---|---|
| **P2** | stderr, CI, ±, **variance across runs/seeds**, or an **explicit statistical qualifier** attached to a reported result | "stderr, confidence interval or error bar AS STATED" | **Yes.** Omits variance-across-seeds and the statistical-qualifier clause. The sheet's own worked example, `std across 3 seeds: 0.6`, is not covered by any of the three terms the prompt names. |
| **P3** | how items were **drawn and how they relate to the population** | "how the evaluated items relate to the full benchmark or to a target population — subset size, sampling method" | Aligned. The prompt's "subset size" is looser than the sheet, which explicitly rules out bare item counts, but the sheet is the stricter side, so it cannot cause a miss. |
| **P4** | temperature, seed, greedy decoding, **n-shot regime with sampling config**, repeat-run policy | "temperature, seed, greedy decoding, number of repeat runs" — with `shot_count` split into its own field | **Partial.** The construct is split across two prompt fields, so a card stating only a shot count populates `shot_count` and leaves `harness_determinism` blank. Consistent with the LMEVAL-P4 ruling, and not a miss source for the enriched four. |
| **P5** | explicit chance or null baseline, incl. **"chance level shown in table"** | "a stated chance/random/majority-class baseline for this benchmark" | **Minor.** A chance level present as a table column rather than as a stated value has no clear home in the prompt's phrasing. |
| **P6** | what decision or deployment context the eval is meant to inform; present includes **"an eval section explicitly tied to an intended-use statement"** | "a stated context of use or decision **this score** is claimed to support" | **Yes, structural.** The prompt asks per-`VALIDATION_RESULT`, i.e. per benchmark score. The sheet labels a **section-level** tie. A card whose eval section is tied to an intended-use statement has no per-score COU for the extractor to emit. |
| **P7** | capability-matched comparisons, partialling, **ablations offered as controls**, or **an explicit limitation statement doing this work** | "any stated control for capability confounds, partialling, or capability-matched comparison" | **Yes.** Omits both ablations-as-controls and limitation-statements entirely — the two forms that produced most of the labeled positives. |

## Each drift predicts its own failure

The three drifted properties are the three with the worst false-fire rates, and
the mechanism is specific in each case rather than a general "the prompt is
vaguer" story:

- **P7 — 100% miss on all three model families.** The prompt never mentions
  ablations or limitation statements. The labeled positives are the `llemma`
  "controlled for model size" pair, the parameter-matched `abacusai` ablation,
  and the `ibraheemmoosa` nine-run transliteration control. The extractor was
  not asked for the category these belong to.
- **P6 — 90–100% miss.** Per-score versus per-section. The extractor emits one
  block per benchmark; a COU stated once for the whole evaluation section
  belongs to none of them.
- **P2 — 21–58% miss.** The prompt omits variance-across-seeds, which is the
  `stefan-it` five-run mean±std family — the largest single cluster of P2
  positives in the stratum.

## What this does and does not establish

**Established:** the measurement compared two constructs. Any extractor-capability
claim drawn from the current table is unsupported, including "a 70B model cannot
read P7" — it was never asked to.

**Not established:** that the sheet's definitions are right. The drift is
symmetric evidence: it says the two documents disagree, not which one is correct.
The sheet's P6 accepts a section-level tie and its P7 accepts an ablation offered
as a control, and both are the labeler's own judgment calls under their own
instructions. Whether the extractor's narrower reading is the *better* one is
step 2, and it is open.

That is why alignment is not automatically "make the prompt match the sheet."
If step 2 finds the extractor's readings defensible, the finding flows backward
into the taxonomy — the property definitions tighten, and the sheet moves toward
the prompt rather than the reverse. That is the A16 finding-validity loop
surfacing at the extraction layer, which is a more valuable outcome than a
prompt bug.

## Consequence for sequencing

Prompt v2 is **not** a fix and must not be framed as one. It is a new pinned
measurement, and it cannot be authored until step 2 settles which set of
definitions is being aligned to. Its definitions and worked examples are then
drawn verbatim from whatever the reconciled instruction sheet says, so the two
documents cannot drift again silently — a single source, quoted, rather than two
paraphrases maintained in parallel.

**The durable lesson, independent of how step 2 lands:** a labeling instruction
and an extraction prompt that define the same property in their own words are
two constructs wearing one name. They must share text, not merely intent.

---

# Step 2 — qualitative read of the 20 P6/P7 misses

Each of the 20 cards `Llama-3.3-70B-Instruct-Turbo` read as silent, put beside
the labeler's `present`, and judged against **the instruction sheet's own text**
— not against a fresh opinion. The question is only: is the extractor's `absent`
defensible under the sheet as written?

**Result: 13 of 20 labels sound, 7 too generous.** Both directions are real, and
the drift is not the whole story.

| | label sound (extractor genuinely missed) | too generous (extractor defensible) |
|---|---:|---:|
| P6 | 6 | 4 |
| P7 | 7 | 3 |
| **all** | **13** | **7** |

## The 13 sound labels — real misses, and the drift explains them

The forms the extractor missed are precisely the forms the prompt omits:

- `EleutherAI/llemma_7b` and its GGUF twin: *"when **controlled for model size**,
  outperform Minerva."* This is the instruction sheet's own worked example, near
  verbatim. The prompt never asks for it.
- `abacusai/Fewshot-Metamath`: LoRA `r=8` chosen *"to match trainable params"* —
  a capability-matched comparison stated outright.
- `ibraheemmoosa/xlmindic-base-uniscript`: compares against an ablation model
  that isolates transliteration; nine runs with mean and std.
- `HeAAAAA/Crab`, `Riser/YOLOP`: ablation tables isolating components.
- P6's sound six all share one shape: **a measurement, then an explicit tie to a
  use context** — *"These metrics demonstrate… making it suitable for Quranic
  transcription"*, *"demonstrated superior accuracy… making it suitable for
  clinical use"*.

On these the extractor is simply wrong, and the cause is documented in step 1.

## The 7 too-generous labels — and they are not definitional disputes

The over-generous calls fall into exactly two patterns, and **both are already
excluded by the sheet's own `Absent` clause**. These are labeling slips against
the instructions, not disagreements with them:

**P6 — model-level use disclaimers counted as a claimed COU (4 cases).**
`AXCXEPT` *"provided for research and development purposes only"*, `Bochkov`
*"Research use only"* under Limitations, `Intel` *"not intended to inform
decisions central to human life"* in an Ethical Considerations table, `arijitx`
*"the primary intended users… are AI researchers"*.

Every one is a statement about the **model**, sitting inside the scoped eval
section by proximity rather than by connection. The sheet already rules this
out: *"a generic intended-use section elsewhere in the card that the eval content
never connects to… The connection must be stated, not inferable."* `arijitx`
additionally names an **audience**, which is the category the NVIDIA-P6 ruling
excluded three cards for.

**P7 — being part of an ablation counted as offering one as a control (3 cases).**
The three `Mr-FineTuner` cards say they hold *"the evaluation results of the base
model… as part of an ablation study"*. Each is one **arm** of an ablation. None
presents a comparison, a matched condition, or any confound analysis; each
reports its own numbers alone. The sheet asks for *"ablations offered as
controls"* — offered, doing the work — not membership in a study conducted
elsewhere.

## What this means for step 3

Both hypotheses were partly right, and the fix is two-sided:

1. **Align the prompt to the sheet** for the 13 sound cases — chiefly P7's
   ablations-as-controls and limitation-statements, P6's section-level tie, and
   P2's variance-across-seeds. This is genuine drift and the prompt is the side
   that is wrong.
2. **Do not loosen the sheet** for the 7. They are already correctly excluded by
   its text; what failed was application, not definition. The remedy is a
   worked negative example per property in the sheet — *"research use only" is
   not a claimed COU; being an arm of an ablation is not offering one as a
   control* — so the same slip is harder to repeat.

The 7 also move the measured rates. On P6 and P7 the labeled positive class is
10 each; removing the over-generous calls leaves **6 and 7**. Both fall below the
protocol's 15–30 target, which returns P6 and P7 to the §6 honest-exit
conversation on a firmer basis than before: not "we could not find positives",
but "we found them, adjudicated them, and this many survived".

## Correction: the keepers claim is three-family, not two

Recorded because I understated it. Reporting the qualification table as
"two vendors" conflated two separate claims:

- The **shared-config qualification table** carries two vendors (Meta,
  DeepSeek), because the Qwen row is excluded on operational scope.
- The **`hard_assert` keepers claim** is **three families**. The local
  `ollama/qwen3.5:4b` row passed **13/13**, recorded in commit `cdcf3f94`
  alongside its own pins, and its backend difference (local Ollama rather than
  the shared OpenAI-compatible path) is the annotation, not a disqualification.

So the trap set's family-independence cites **Qwen, Llama and DeepSeek**. The
two claims travel separately and both survive: the qualification table is the
pinned record of what was run and asserts nothing about capability, while the
keepers result is a property of the case set that held across every extractor
tried, including the two whose rates were otherwise failing everything.

**Neither number is authoritative yet.** This read is one pass by the same agent
that drafted the labels, which is the weakest possible adjudication and is
recorded as such. It is the input to A16.4's panel, not a substitute for it.
