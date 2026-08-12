# Confirm: 7 label flips, `present` → `absent`

**For author confirmation.** Each row is a label I read as too generous against
the instruction sheet's own `Absent` text. Confirming converts same-agent
adjudication into author-confirmed on the subset that moves the denominator:
P6 falls 10 → 6 positives, P7 10 → 7.

Mark each **confirm** or **keep**. A `keep` costs nothing — it means the label
stands and my read was wrong, which is itself the finding.

The clause cited is quoted verbatim from
`docs/A16_3_gold_labeling_instructions_v0_1.md` §2.

---

## P6 `claimedCOU` — 4 flips

All four are **model-level use statements** that sit inside the scoped eval
section by proximity, not by connection.

**The clause each fails:**
> **Absent:** a generic intended-use section elsewhere in the card that the eval
> content never connects to; benchmark scores presented without any statement of
> what they are evidence FOR. **The connection must be stated, not inferable.**

| # | Card | What it says (verbatim) | Why it fails the clause | ☐ confirm / ☐ keep |
|---|---|---|---|---|
| 1 | `AXCXEPT/EZO-Llama-3.2-3B-Instruct-dpoE` | "This model is provided for research and development purposes only… **not intended for commercial use** or deployment in mission-critical environments." | A `[Disclaimer]` block about the model. No eval result is tied to it. | |
| 2 | `Bochkov/max_bvv_moe` | "Limitations. Research use only… SFT was only lightly applied; **not intended for real world use**." | Under **Limitations**, describing training coverage. Never connects to a reported score. | |
| 3 | `arijitx/whisper-base-bn-trans` | "The primary **intended users** of these models are AI researchers studying robustness, generalization, capabilities, biases…" | Names an **audience**, not what the evaluation supports. Same category the **NVIDIA-P6 ruling** excluded 3 cards for ("it names an audience, not a claim about what the evaluation supports"). Inherited Whisper card boilerplate. | |
| 4 | `Intel/bert-base-uncased-sparse-85-unstructured-pruneofa` | "\| Human life \| The model is **not intended to inform decisions central to human life** or flourishing. \|" | A row in an **Ethical Considerations** table. A use boundary on the model, not a claim about the evaluation. | |

**Note on 1, 2 and 4:** these are the "negative COU" cases you flagged as among
the strongest P6 positives. The distinction I am drawing is *not* that a negative
COU fails to count — `EnjoyCodeX/MedLang-13B` ("…render the current MedLang-13B
unsuitable for deployment in practical medical applications") is retained as
`present`, because there the eval discussion is what leads to the ruling. These
four state a boundary on the **model** with no eval content attached. If you read
the boundary itself as sufficient regardless of connection, these are `keep` and
the sheet's clause needs rewording instead.

## P7 `confoundControlStatement` — 3 flips

All three are the same card template, one per base model.

**The clause each fails:**
> **Present:** capability-matched comparisons, partialling, **ablations offered
> as controls**, or an explicit limitation statement doing this work ("gains
> persist after controlling for model size").

| # | Card | What it says (verbatim) | Why it fails the clause | ☐ confirm / ☐ keep |
|---|---|---|---|---|
| 5 | `Mr-FineTuner/Test_02_noFinetune_LLaMA_myValidator` | "This repository contains the evaluation results of the base `unsloth/llama-3-8b-instruct-bnb-4bit` model… without fine-tuning, **as part of an ablation study**." | Declares **membership** in an ablation. The card presents this arm's numbers alone — no comparison, no matched condition, no confound analysis. | |
| 6 | `Mr-FineTuner/Test_02_noFinetune_Mistral_myValidator` | same, `unsloth/mistral-7b-instruct-v0.3-bnb-4bit` | same | |
| 7 | `Mr-FineTuner/Test_02_noFinetune_myValidator` | same, `unsloth/gemma-7b-bnb-4bit` | same | |

**The distinction:** the sheet asks for an ablation *offered as a control* —
doing the confound work in this card. These are one **arm** of a study conducted
elsewhere. Retained as `present` for contrast: `ibraheemmoosa` ("we compare with
an ablation model that does not use transliteration"), `abacusai` ("LoRA `r=8`
**to match trainable params**"), `HeAAAAA/Crab` (w/o base / w/o ref / w/o scene
table), `Riser/YOLOP` (End-to-end v.s. Step-by-step table).

If you read "as part of an ablation study" as sufficient — the card *is* the
control condition, and its numbers exist to be compared — these are `keep`.

---

## What happens on confirm

1. The 7 flip in `enriched_labels.csv` as **dated adjudicated corrections**, each
   citing the clause above, with the prior value retained in the note.
2. `cases.json` rebuilds; the 7 move from `expected=present` to
   `expected=absent`. None carries `hard_assert` — those stay mechanical.
3. v1 rates rebuild against corrected labels, **before** prompt v2 runs, so v2
   is measured on corrected ground rather than crediting the fix twice.
4. P6 and P7 positive classes become 6 and 7 — both under the protocol's 15–30
   target, returning them to the §6 honest-exit conversation with adjudicated
   numbers rather than a failed search.
