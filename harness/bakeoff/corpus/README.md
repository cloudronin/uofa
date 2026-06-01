# Bakeoff corpus — answer-keyed, D-category-stratified (SEED)

This directory holds the Gate's answer-keyed rows. Each `*.json` carries the
four-field key (`gold_mechanism`, `gold_action` §5B, `forbidden_claims`,
`acceptable_confidence`) and per-field `label_provenance`.

**This is a growing slice, not the full corpus.** Six rows are committed, each
answer key grounded in a real, citable source (see each row's `label_provenance`;
mechanism = paper/solver-grounded, disposition = `selection_basis: adjudicated`,
`not_sourced_from` = pipeline/frontier):

| Row | D-category (Jakeman) | Polarity | Grounding |
|---|---|---|---|
| `surr-dx02-carbench-0142` | D5/applicability (§5A) | fire | CarBench + DrivAerML — dangerous-OK wheel-housing |
| `surr-dx02-carbench-0307-control` | D5/applicability | suppress | matched accept-control |
| `surr-dpd02-airfrans-extrap` | D-PD-02 (envelope) | fire | AirfRANS (NeurIPS 2022) — Reynolds/AoA extrapolation |
| `surr-dver06-fno-resolution` | D-VER-06 (verification) | fire | FNO failure modes (arXiv:2601.11428, 2601.08404) |
| `surr-dval09-ensemble-uq` | D-VAL-09 (prediction UQ) | fire | deep-ensemble UQ (arXiv:2007.08792, 2602.11090) |
| `surr-dval09-ensemble-uq-control` | D-VAL-09 | suppress | matched accept-control (recalibrated UQ) |

The controls measure **over-action**.

## Two honesty flags before this doubles as the disposition-gate slice

**1. Dispositions are `provisional-self-adjudicated`, not independent.** The
mechanism fields are paper/solver-grounded, but the gold §5B *actions* are the
row-builder's reasoning (`selection_basis: provisional-self-adjudicated`). That
is fine for an **explanation-gate preview** — the explanation key leans on the
grounded mechanism — but it is **not** a valid disposition-gate seed: a
disposition gate scored against self-adjudicated gold would test whether one
model reproduces another model's reasoned action (the tautology one level up).
Before promotion, the gold actions need **expert- or solver-truth-derived**
adjudication. Do not let `adjudicated` stand in for *independently* adjudicated.

**2. These rows are not yet hardened.** A hard cell is one where the obvious
feature points the *wrong* way (the §5A dangerous-OK case: global pass → "looks
fine," but locally inadequate). Most of the current `D-PD-02 / D-VER-06 / D-VAL-09`
rows are still latchable from a single obvious feature that points the *right*
way (e.g. `evaluationPointInEnvelope: false`), which makes them **easy** and
would **inflate a clear**. The growth target is a few dozen **conflicting-signal**
cells, not more easy ones. Read any small-N result as a **preview** (`gate_read`
flags `preview` below `min_hard_core_n`): a clear routes to *grow-and-rerun*, not
to "commodity → disposition."

**The full hard slice is the expensive curation** (plan: "does not accelerate").
Per the plan + the disposition-gate addendum, grow it concentrated on the hard
cells — dangerous-OK, multi-coherent §5B, accept-controls — with answer keys
grounded in **solver truth / source-paper mechanism / expert adjudication**,
**never** the pipeline's own output or a frontier draft (tautology guards, SLM
spec §5). Disposition selections are expert-adjudicated; that irreducibility is
the moat (addendum). Stratify on **D-category × measure-type × domain ×
fire/suppress**, not pattern ID.

Run: `python -m harness.bakeoff.run_p0 --corpus harness/bakeoff/corpus`
