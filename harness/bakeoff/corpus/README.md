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

The dangerous-OK + multi-coherent rows carry `coherent_alternatives` +
`selection_basis: adjudicated`, so they double as the **disposition-slice** seed
(addendum). The controls measure **over-action**.

**The full hard slice is the expensive curation** (plan: "does not accelerate").
Per the plan + the disposition-gate addendum, grow it concentrated on the hard
cells — dangerous-OK, multi-coherent §5B, accept-controls — with answer keys
grounded in **solver truth / source-paper mechanism / expert adjudication**,
**never** the pipeline's own output or a frontier draft (tautology guards, SLM
spec §5). Disposition selections are expert-adjudicated; that irreducibility is
the moat (addendum). Stratify on **D-category × measure-type × domain ×
fire/suppress**, not pattern ID.

Run: `python -m harness.bakeoff.run_p0 --corpus harness/bakeoff/corpus`
