# Bakeoff corpus — answer-keyed, D-category-stratified (SEED)

This directory holds the Gate's answer-keyed rows. Each `*.json` carries the
four-field key (`gold_mechanism`, `gold_action` §5B, `forbidden_claims`,
`acceptable_confidence`) and per-field `label_provenance`.

**This is a SEED, not the full slice.** Two rows are committed to exercise the
harness end-to-end:

- `surr-dx02-carbench-0142.json` — the **dangerous-OK** §5A case (global-pass /
  local-inadequate wheel-housing): the action is not obvious from the firing
  alone, and a naive model says "looks fine." `gold_action` is built
  **adjudication-ready** (`coherent_alternatives` + `selection_basis: adjudicated`)
  so it doubles as the **disposition-slice** seed (addendum).
- `surr-dx02-carbench-0307-control.json` — the matching **control**: the region
  IS characterized, so the correct disposition is *accept* — it measures
  **over-action**.

**The full hard slice is the expensive curation** (plan: "does not accelerate").
Per the plan + the disposition-gate addendum, grow it concentrated on the hard
cells — dangerous-OK, multi-coherent §5B, accept-controls — with answer keys
grounded in **solver truth / source-paper mechanism / expert adjudication**,
**never** the pipeline's own output or a frontier draft (tautology guards, SLM
spec §5). Disposition selections are expert-adjudicated; that irreducibility is
the moat (addendum). Stratify on **D-category × measure-type × domain ×
fire/suppress**, not pattern ID.

Run: `python -m harness.bakeoff.run_p0 --corpus harness/bakeoff/corpus`
