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
