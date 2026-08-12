# Confirm: label queue batch 2 — 15 rows

**For author confirmation.** Same format as the seven-flip table. Mark each
**confirm** or **keep**; a `keep` means the label stands and my read was wrong,
which is itself the finding.

13 of the 15 are one house sentence and clear as a single class decision. The
batch is 3 decisions, not 15.

Clauses quoted verbatim from `docs/A16_3_gold_labeling_instructions_v0_1.md` §2.

---

## CLASS-SEALION-P5 — 13 rows, one decision. P5 `present` → `absent`

**The clause:**
> **P5 Present:** an explicit chance or null baseline for at least one reported
> result ("random baseline: 25%", "majority-class: 51%", "chance level shown in
> table").
> **P5 Absent:** … "significantly above chance" **with no stated chance value**
> MAY be `unclear` — see §3.

**What all 13 say** (identical sentence, one organization's house style):

> "The scores for each task is normalised to account for **baseline performance
> due to random chance**."

or its variant:

> "…normalisation is performed to account for **baseline performance due to
> random chance**."

**Why it fails:** it names chance and **states no baseline value**. Every Present
example carries one. The card asserts the scores were *adjusted* for chance, not
what chance *was* — a reader cannot recover the null from this sentence.

**The 13 rows:**

| # | Card |
|---|---|
| 1 | `Sahabat-AI/Llama-Sahabat-AI-v2-70B-IT` |
| 2 | `GoToCompany/gemma2-9b-cpt-sahabatai-v1-instruct` |
| 3 | `GoToCompany/llama3-8b-cpt-sahabatai-v1-instruct` |
| 4 | `GoToCompany/llama3-8b-cpt-sahabatai-v1-base` |
| 5 | `aisingapore/Llama-SEA-LION-v3-8B-IT` |
| 6 | `aisingapore/Llama-SEA-LION-v3-8B` |
| 7 | `aisingapore/Llama-SEA-LION-v2-8B-IT` |
| 8 | `aisingapore/Llama-SEA-LION-v3.5-70B-R` |
| 9 | `aisingapore/Llama-SEA-LION-v3.5-8B-R` |
| 10 | `aisingapore/Llama-SEA-LION-v3-70B` |
| 11 | `aisingapore/Gemma-SEA-LION-v3-9B` |
| 12 | `QuantFactory/gemma2-9b-cpt-sea-lionv3-instruct-GGUF` |
| 13 | `humane-intelligence/gemma2-9b-cpt-sealionv3-instruct` |

☐ **confirm all 13 → absent**  ☐ **keep all 13 → present**  ☐ **unclear** (if the
normalization claim is judged to *imply* a null without stating one)

**Note:** a `keep` here is defensible on the reading that normalizing *for* chance
presupposes a known chance level, so the property is satisfied even where the
number is not printed. That reading would need the sheet's Present clause
reworded, since none of its examples work that way. `unclear` is also available
and §3 anticipates exactly this shape.

## rmtariq — 1 row. P5 `present` → `absent`

| Card | What it says | Why it fails |
|---|---|---|
| `rmtariq/malaysian-priority-classifier` | "### Benchmark Comparison — **vs Random Baseline**: +66% accuracy improvement" | A **relative delta**, not a baseline. +66% *over* an unstated null tells you the gap, never the null. Same failure as the class above, different phrasing. |

☐ confirm → absent  ☐ keep → present

**Kept as `present` for contrast:** `m-a-p/ChatMusician` — "the dashed line
corresponds to a random baseline, **with a score of 25%**" — states the value and
is a clean Present. It is not in this queue.

## ibraheemmoosa — 1 row. P2 `absent` → **`present`**

**The only flip in this direction all session.** Every other correction has been
`present` → `absent`; this one adds a positive.

| Card | What its table says | Why the label looks wrong |
|---|---|---|
| `ibraheemmoosa/xlmindic-base-uniscript-soham` | `Wikipedia Section Title Prediction \| 71.90 \| 65.45 \| 69.40 \| **81.78 ± 0.60** \| 77.17 ± 0.76` | `± 0.60` on the **bolded** subject column is a textbook P2 Present ("stderr, CI, ±… attached to a reported result"). The row carries **no `P2_note`**, so no reasoning was recorded against it. Its sibling card `ibraheemmoosa/xlmindic-base-uniscript` states "the mean and standard deviation of **nine fine-tuning runs**", and is labeled P2 `present`. |

☐ confirm → present  ☐ keep → absent

**Two cautions on this one.**

First, **the card id.** Your note said `xlmindic-base-multiscript`; the case in
the set is `xlmindic-base-uniscript-soham`. `-multiscript` is a *different* card,
referenced inside the uniscript card as its ablation comparator. Worth one look
that we are correcting the row you meant.

Second, **how it was found.** The keyless route flagged it — the route disagreed
with the label, and on inspection the label looks wrong. That is a route
criticizing its own ground truth, which is exactly the circularity the holdout
gate exists to prevent. If confirming it feels like letting the tool grade its own
exam, `keep` is the safe call and costs one case out of 24.

---

## What confirming changes

- **P5 positives: 20 → 6** (or 7 if `unclear` is chosen for the class, which
  removes them from both denominators rather than moving them to absent).
- **P2 positives: 33 → 34**, with the table-borne cell going 24 → 25.
- Both feed the **holdout gate denominators** and the re-scoped fork, which is
  why this batch is first in the order of operations.

Nothing is flipped until this comes back.
