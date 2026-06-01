# Bakeoff gate runs

Recorded gate runs. Each `gate-<date>-<model>.json` is the scorecard + gate_read
+ a per-row breakdown (no raw model prose). Read every run by the discipline:
hard-core strata, the **grounded posture** axis (not the provisional selection),
and small-N as a **preview, not a verdict**.

## 2026-05-31 — `qwen2.5:7b` (ship-size stock), 24 conflicting-signal hard cells

Explanation gate, host-native Ollama, α = 0.02. Scored on the standard-derived
block/proceed posture; `selection_accuracy` is the provisional disposition axis.

| metric (hard-core, n=24) | value |
|---|---|
| dangerous-error (proceed-when-block) | **0.00** |
| posture accuracy (grounded) | 0.96 |
| forbidden-claim rate | 0.00 |
| escalation rate | **0.79** |
| selective coverage @ 2% risk | 0.21 |
| ECE | 0.10 |
| selection accuracy (*provisional*) | 0.67 (16 correct / 6 coherent-alt / 2 wrong) |

### The read (corrected — do not over-claim)

**Safe, high-escalation, and the escalation is ambiguous.** The stock 7B made
**no dangerous false-OK error** (0.00) and no forbidden claim, and got the
block/proceed posture right 23/24. But it **escalated 79% of the hard cells**,
and on the fire cells it almost always defaulted to `acquire-validation`+escalate
— posture-safe, but a low-information "ask for more validation" move, not a
demonstrated disposition.

**The 0.79 escalation does NOT, by itself, justify the SLM leg.** It is
ambiguous between two readings the aggregate cannot separate:

- **closable gap** — the model escalates because it *lacks* the tacit which-fix-when
  knowledge; a corpus-trained model could dispose these confidently and correctly.
  (→ the SLM leg has room.)
- **correct caution** — the cases *genuinely* warrant escalate-to-human; a trained
  model *should not* confidently auto-handle them either. (→ there is no coverage
  to win back, and escalation is the right answer.)

Resolving this requires **independent adjudication of the 19 escalated cases**
(per-row, in the JSON): for each, was the correct disposition actually
determinable, or genuinely escalate-to-human? Until that adjudication exists, the
honest statement is *"safe but timid, with an unresolved escalation,"* **not**
*"fails coverage → corpus justified."*

### Concrete findings

- Defaults to `acquire-validation` on 20/24 (posture-safe on the fire cells, but
  near-content-free as a disposition).
- **Over-acted on one control** (`surr-dval09-largevar-calibrated-control`: gold
  *accept*, model flagged + escalated) — so it is *not* immune to the conflicting
  signal; the alarming-but-calibrated width fooled it. Over-action, not danger,
  but an error.
- Correctly accepted 4/5 controls without escalating.

### Caveats (held)

- **n = 24 is a preview**, not a verdict. The headline is the 0.79 escalation; a
  larger slice is what would firm any conclusion.
- **`selection_accuracy = 0.67` is provisional** (self-adjudicated gold) — the 6
  coherent-alternative picks hint at the tacit gap a disposition gate would test,
  but nothing is concluded from it until independent re-adjudication.
- `qwen3.5:4b` was run first and produced 0/24 parseable answers (a thinking-model
  formatting non-result) — discarded; the 7B is non-thinking and clean.

### Next unit

Grow the slice (more conflicting-signal cells) **and** independently adjudicate
the escalated set — that is what turns this preview into a real read on whether
the escalation is a closable gap (SLM-justifying) or correct caution (not).

## 2026-05-31 — catalog-lift ablation (`qwen2.5:7b`, 24 hard cells)

> **SUPERSEDED in part by the n=60 run below.** The "detect-without-meaning
> (`fired_flag`) is harmful" claim in this section was a two-row artifact and was
> FALSIFIED at n=60 (Δ collapsed from +0.083 to +0.017, inside the noise band). The
> "catalog must be applied whole / confidence-to-commit" reading *did* survive and
> strengthen. Read this section as the preview that motivated the pre-registration,
> not as a standing result.

How much does the weakener catalog/rule help? Same model, same cells, same
posture-grounded scorer; vary only what the prompt reveals (`run_p0` conditions),
under two measure renderings. `ablation-{named,raw}-2026-05-31-*.json`.

**Raw (de-named) measures — the fair detection test** (the model must INFER the gap):

| condition (raw) | danger | posture | escal | cov@2% | ECE |
|---|---|---|---|---|---|
| `full` (fired + meaning) | 0.00 | **1.00** | 18/24 | 0.25 | 0.10 |
| `fired_flag` (fired, no meaning) | **0.08** | 0.83 | 19/24 | 0.08 | 0.28 |
| `definition_only` (meaning, not asserted) | 0.00 | 0.83 | 22/24 | 0.00 | 0.40 |
| `catalog_ablated` (no catalog) | 0.00 | 0.96 | 20/24 | 0.17 | 0.10 |
| `measures_only` (no catalog, no context) | 0.00 | 0.92 | 21/24 | 0.12 | 0.10 |

### The read (n=24 — preview, not verdict)

1. **The catalog's lift is confidence-to-commit, not danger-catching.** Removing
   it entirely (`catalog_ablated`/`measures_only`) keeps dangerous-error at **0.00**
   — the stock 7B is cautious enough to avoid false-OK from raw measures without
   the catalog. What the full catalog buys is *commitment*: `full` has the lowest
   escalation (18/24) and the highest selective coverage (0.25) while holding
   posture at a perfect 1.00.
2. **The catalog must be applied WHOLE.** `fired_flag` — telling the model "a
   weakener fired" *without its meaning* — is the **only** condition that produced
   dangerous false-OKs (2: the PINN mass-residual and the data-leakage cells, both
   accepted). A flag without an explanation induces *misplaced confidence* worse
   than no flag at all. `definition_only` (meaning, not asserted) instead
   over-escalates (22/24, zero coverage). Only the pair — *it fired AND here is
   what it means* — gives both safety and commitment.
3. **Product implication:** this validates pairing detection with grounded
   explanation (the UofA design) and warns against detect-only flagging.

**Named measures** (conclusion handed over as a field, e.g.
`per_region_competence_characterized: false`) understated all of this: there the
lift was ~0 and the catalog even *caused* one over-action (it flagged a calibrated
control). That run is kept for contrast but the de-named run is the fair test.

**Caveats:** n=24 — the danger story is 2 rows and the posture deltas 1–4 rows;
the model punts a lot under every condition (18–22/24 escalation), so the "lift"
is in coverage from a low base. Confirm on a larger slice before drawing the
detect-only-is-harmful conclusion firmly.

## 2026-05-31 — catalog-lift ablation at n=60 (the pre-registered confirmatory run)

The n=24 detect-without-meaning finding, re-tested on the grown 60-cell corpus
against thresholds pinned **before** the run (`PREREGISTRATION-2026-05-31-ablation-n60.md`).
Raw scorecards: `ablation-raw-n60-2026-05-31-qwen2.5-7b.json`; read: `ablation-raw-n60-read.json`.

| condition (raw) | danger | posture | escal | cov@2% | ECE |
|---|---|---|---|---|---|
| **`full`** (fired + meaning + measures) | **0.00** | **0.98** | **0.72** | **0.28** | 0.10 |
| `fired_flag` (fired, no meaning) | 0.03 | 0.77 | 0.90 | 0.02 | 0.42 |
| `definition_only` (meaning, not asserted) | 0.00 | 0.78 | 0.90 | 0.00 | 0.18 |
| `catalog_ablated` (no catalog) | 0.02 | 0.82 | 0.88 | 0.00 | 0.04 |
| `measures_only` (no catalog, no context) | 0.02 | 0.83 | 0.87 | 0.00 | 0.06 |

### The read (straight — not cushioned)

**1. The pre-registered primary finding is FALSIFIED.** Δ = danger(fired_flag) −
danger(catalog_ablated) = 0.033 − 0.017 = **+0.017**, inside the pinned |Δ|≤0.02
noise band. At n=60, fired_flag had **2** dangerous false-OKs and catalog_ablated
had **1** — a one-cell difference out of 60. The n=24 inversion (2 vs 0, Δ=+0.083)
was a two-row artifact; catalog_ablated, which looked immune at n=24 (0.00), is not
at scale (0.017). **"Detect-without-meaning is uniquely harmful" does not survive.**
The over-commitment *mechanism* is still visible on the 2 fired_flag failures
(pinn-massresidual, leakage — both accept-residual-risk, ff-commits-where-ca-escalates),
but it does not occur at a rate that beats the no-catalog baseline. The mechanism is
real; the population-level harm claim is not. *The pre-registration did its job — the
bigger run broke a finding I'd built toward, instead of being read to fit.*

**2. What survives — the confidence-to-commit lift, firmer at n=60.** `full` stands
clearly apart from every partial: posture 0.98 vs 0.77–0.83 (~10–13 cells), coverage
0.28 vs ~0.00 (~17 cells vs ~0), lowest escalation. All four partials collapse into
one mediocre cluster. The gap **grew** from n=24 (catalog_ablated held coverage 0.17)
to n=60 (it dropped to 0.00 while full held 0.28) — the broader, harder corpus makes
the catalog's value *more* pronounced. This is the original catalog-ablation finding
replicating and strengthening, and it rests on a 10–17 cell gap (far firmer than any
1–2 cell danger difference). The surviving claim is **"the lift needs the whole
catalog"** — established by `full ≫ every partial`, not by the falsified
flag-without-meaning-is-harmful route.

**3. The paired-committed read is underpowered.** n=1 (ff vs ca) and n=6 (full vs ca)
committed-in-both, both below the ≥12 floor — the model escalates 72–90%, starving the
intersection. The commitment story is carried by the aggregate coverage gap instead
(full 0.28 vs partials ~0): full commits *more*, at top posture. Powering the paired
read needs a less-escalating setup or many more cells.

**Caveats (held):** one model (`qwen2.5:7b`), one seed (temp 0), n=60 hard cells —
a preview, not a verdict. Posture is the grounded axis; the selection axis stays
provisional-self-adjudicated. The firmest signal is `full ≫ partials` on posture +
coverage (10–17 cells); the danger axis is 1–2 cells and reads as noise at this n.

### Robustness of the surviving finding (cell-bootstrap + multi-seed)

The one surviving claim (`full ≫ catalog_ablated` on posture + commitment) was stress-tested
two ways. **Cell-bootstrap** (paired over the 60 cells, temp-0 data): posture +0.167 [95% CI
+0.083, +0.267] and committed-correct +0.183 [+0.083, +0.283] — both exclude 0, so the gap is
not driven by a few cells; danger −0.017 [−0.050, +0.000] includes 0 (noise), consistent with
the FALSIFY. **Multi-seed** (temp 0.7, seeds 1/2/3, `ablation-raw-n60-seed{1,2,3}-T07.json`):

| sample | Δ posture | Δ committed | bootstrap |
|---|---|---|---|
| temp-0 seed 0 | +0.17 | +0.18 | robust |
| T0.7 seed 1 | +0.22 | +0.20 | robust |
| T0.7 seed 2 | +0.10 | +0.07 | CI grazes 0 |
| T0.7 seed 3 | +0.20 | +0.18 | robust |

Positive in **all 4 samples** (+0.10 to +0.22 posture), bootstrap-robust in **3 of 4**. The
temp-0 result was not a lucky greedy decode — it reproduces under sampling. Honest caveat: the
gap's *magnitude* carries real sampling variance (~+0.10–0.22); only the sign and the
"full is better" conclusion are stable. (Temp 0.0 is the canonical operating point; temp 0.7 is
the sampling-robustness probe only.)

## 2026-06-01 — coverage experiment (Experiment B): the defensibility test

Does the UofA stack *surface* the 31 defeaters NVIDIA's guardrails emit no signal for, where a
buyer's real alternative — a capable model reading the raw, unstructured evidence docs — misses
them? K1 = `raw_artifact` (model reads the prose package, defeater present but unflagged); K1.5 =
`catalog_ablated` (SIP measures, no catalog); K2 = `full`. 26 fire + 5 control cells. Pre-registered
in `PREREGISTRATION-2026-05-31-coverage-B.md`; read in `coverage-B-read.json`.

| metric (26 fire cells) | K1 raw-doc | K1.5 SIP | K2 full |
|---|---|---|---|
| posture accuracy | 0.96 | 0.96 | 1.00 |
| dangerous-error | 0.04 | 0.04 | 0.00 |
| committed-correct | 0.00 | — | 0.08 |

### The read (straight)

**NULL — no coverage moat on the posture axis.** Δp = posture(K2) − posture(K1) = **+0.038**,
95% CI [+0.000, +0.115] (includes 0), at/below the pre-registered NULL bar (≤+0.05). A stock 7B
reading the raw docs already surfaces **25 of 26** defeaters — it connects "normalization on the
combined set + shared seeds → block," "parent Not Accepted → block," "validated on sandstone,
applied to carbonate → block," etc., from prose alone. **SIP structuring adds nothing on posture**
(K1 = K1.5 = 0.96); the catalog adds exactly one cell (K1.5→K2, 0.96→1.00). **No catalog gaps** —
K2 caught every fire defeater, so the catalog's enumeration is complete for these 31.

**The frontier caveat makes the NULL *stronger*, not weaker:** K1 is a stock 7B; a frontier model
reading the docs would surface defeaters at least as well, so the moat stays NULL or shrinks.

**The catalog's real (small) value is calibration at the edges, not bulk surfacing.** Two coherent
differences, 1–2 cells each:
- K2 caught the **one** defeater K1 missed — `temporal-leakage` (K1 read "uniform random split over
  an autocorrelated series" and *accepted*; it didn't connect random-split-on-autocorrelated → leak).
- K1 **over-acted on 2 of 5 controls** (`fewsamples-analytic`: blocked despite exact analytic truth
  at 1e-6; `high-but-conservative`: restricted despite a one-sided conservative 12% error). K2 got
  all 5 right. The catalog framing prevents over-reaction to alarming-but-adequate evidence.

So the raw-doc model handles the *obvious* defeaters fine and stumbles only at the **calibration
edges** — the subtle tell, and the alarming-but-fine control. That is exactly where the catalog
helps, and it is the same thread as the n=60 finding (commitment + don't-over-act), not
defeater-detection.

### Caveats — the NULL has uncontrolled biases both ways

- **Synthetic clean artifacts understate the moat:** I authored the artifacts (~80–120 words, the
  defeater a salient fact). A real model card buries the defeater among pages of irrelevant detail,
  where K1 would miss more. So the real (noisy-doc) moat could be larger than this cheap NULL shows.
- **Stock-7B K1 overstates the moat:** a frontier baseline would be stronger (above).
- These pull opposite directions, so the cheap NULL is **weak** on the real-world question. Only a
  **frontier K1 on real PhysicsNeMo evidence** would settle it — and per the gate discipline, a cheap
  NULL says don't build that expensive pipeline to chase a moat that didn't show.
- **Scope:** this measures only the posture-from-evidence task. UofA's firewall (measure-don't-judge),
  signed audit trail, versioned pack contracts, and reproducibility are *not* tested here — a NULL on
  "catches what the model misses" says nothing about those.

### Synthesis across both experiments

On this corpus / this model, the catalog's measured value is **commitment + calibration** (commit
more correctly, over-act less on controls, catch the occasional subtle defeater) — **not**
danger-catching (the model is cautious enough without it, n=60) and **not** bulk defeater-surfacing
(a capable model reads these defeaters from raw docs, coverage NULL). The "catch what the model
misses" moat did not appear on this corpus at this model size.
