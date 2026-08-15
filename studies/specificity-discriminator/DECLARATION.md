# Model or temperature? Declared before the run

The standing question after two independent prompt-side refutations.

## Why this is the remaining explanation

The extractor's specificity collapsed across the C3 hosted-model migration on
two separate fields:

| | qwen3.5:4b | Llama-3.3-70B |
|---|---|---|
| acceptance criteria, distinct/filled | 0.937 | 0.443 |
| claim density | 0.565 | 0.188 |

**Prompt has been refuted twice, independently.**

1. **The pack split.** The `"or implied"` licence exists only in the NASA
   prompt. Both packs collapsed by nearly the same amount — nasa −0.448 with the
   clause, vv40 −0.405 without it. A clause absent from the vv40 prompt cannot
   explain the vv40 collapse.
2. **Q2.** A prompt change aimed directly at claim density **halved** it,
   0.1875 → 0.0854, and left the real corpus at 0.000.

What remains is the model itself, or the sampling temperature, and those have
never been separated because the migration changed both at once.

## The arms

Four runs, on the 30-bundle synthetic dev split, **identical prompts**
throughout — the current committed prompts, unmodified.

| arm | model | temperature |
|---|---|---|
| A | `ollama/qwen3.5:4b` | current default |
| B | `ollama/qwen3.5:4b` | 0.0 |
| C | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | current default |
| D | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | 0.0 |

C is the current pipeline and its figures are already measured
(`studies/hosted-model-specificity/`); it is re-run anyway so all four come from
one session with one prompt version.

## Expected signatures, written before the run

**If the cause is the MODEL:**
A and B both show high specificity; C and D both show low. The gap tracks the
model column and barely moves down the temperature column. Concretely,
`|A − B|` and `|C − D|` are both small relative to `|A − C|`.

**If the cause is TEMPERATURE:**
B and D converge. Whatever temperature the hosted runs use is the thing
producing generic prose, and pinning it to 0 recovers specificity in both
models. The gap tracks the temperature column.

**If it is an interaction:**
B recovers and D does not, or vice versa. This is the awkward outcome and it is
named in advance so it cannot be reported as one of the clean two: it would mean
the models respond differently to the same temperature, and the recovery path
becomes model-specific.

**If nothing separates them:**
All four cluster. That would mean the collapse is neither model nor temperature
as operationalised here, and the question returns to the corpus or the
measurement — with the standing caution that the metric under-counts by ~1%
(see task #20) which is far too small to explain a 0.5 gap.

## Thresholds

**Primary measure: acceptance-criteria distinct/filled**, corpus-wide, on the 13
shared V&V 40 factors. It is the cleanest of the two collapsed fields — it needs
no claim tokeniser and is not subject to the trivial-integer defect.

- **Model-attributed** if `|A − C| ≥ 0.20` **and** both `|A − B| < 0.10` and
  `|C − D| < 0.10`.
- **Temperature-attributed** if `|C − D| ≥ 0.20` **and** `|A − C| < 0.10`.
- **Interaction** if neither holds and any pair differs by ≥ 0.20.
- **Unseparated** if no pair differs by ≥ 0.20.

0.20 is half the observed collapse (≈0.45), so an effect must account for at
least half the gap to claim it.

**Secondary, reported not gating:** claim density and the full groundedness
triple for all four arms. Reported because the triple is never quoted as one
number and because claim density is the field Q2 failed on; not gating because
it inherits the trivial-integer defect.

## What no result licenses

**A pass does not identify a fix.** "The model is the cause" makes recovery an
extraction-model decision — a different and cheaper conversation than prompt or
detector work — but it does not say which model, and qwen was measured worse on
other axes, which is why the migration happened.

**No arm is added after seeing these four.** If the answer is an interaction or
unseparated, that is the answer.

## Cost and feasibility risk, stated in advance

qwen3.5:4b is local and slow — roughly 170–200 s per bundle when last measured,
so arms A and B are on the order of 3–4 hours together for 30 bundles. If the
local model is unavailable or the runtime is prohibitive, **the honest outcome
is that the discriminator was not run**, recorded as such. Substituting a
different local model would change the question from "was it this migration" to
"is it some model", which is not what is being asked.
