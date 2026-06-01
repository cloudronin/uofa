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
