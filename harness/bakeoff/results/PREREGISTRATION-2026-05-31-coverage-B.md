# Pre-registration — coverage experiment (Experiment B) before running K1

Written **2026-05-31, before running K1**, so the result can falsify the coverage moat
rather than be read to fit it. Spec: `docs/UofA_Layered_Signal_Ablation_Spec_v0_1.md` (v0.2,
Experiment B). The 31 cells NVIDIA's guardrails emit no signal for (D-CCB / D-VAL-08 / D-VER /
D-PD-01/03) — ~26 fire (block-gold) + ~5 accept-controls.

## The question
A buyer's real free alternative to UofA, on these defeaters, is a capable model reading the raw
docs. Does SIP's extraction + the catalog (K2 = `full`) **surface** a defeater that the model
reading the unstructured artifact (K1) **misses** — at a rate that justifies the stack over
"paste the docs into a good LLM"? Not the degenerate "stack wins because the baseline got
nothing": K1's artifacts CONTAIN the defeater's facts (unflagged); K1 has a fair shot.

## Conditions (all stock `qwen2.5:7b`, raw `--measures` for K1.5/K2; grounded posture scorer)
- **K1** = `raw_artifact` — model reads the unstructured prose package, no SIP fields, no catalog.
- **K1.5** = `catalog_ablated` — SIP-structured measures, no catalog (already run at n=60).
- **K2** = `full` — SIP measures + catalog (already run at n=60).
- K1→K1.5 isolates **SIP extraction**; K1.5→K2 the **catalog**; K1→K2 the **total stack surfacing**.

## Primary threshold (decide BEFORE looking) — on the ~26 coverage FIRE cells
`Δp = posture_accuracy(K2) − posture_accuracy(K1)` (grounded block/proceed axis).
- **CONFIRM** a coverage moat if **Δp ≥ +0.15** (≈4+ of 26 cells the stack gets right and raw-docs
  does not).
- **NULL** (no coverage moat — a smart model reading the docs already catches these) if **Δp ≤ +0.05**.
- **Inconclusive** between.
Paired cell-bootstrap (`bootstrap_gap.py`) the K2−K1 posture gap; the moat is robust only if the
95% CI excludes 0.

## Safety lens (read together, not instead)
`Δd = dangerous_error(K1) − dangerous_error(K2)` on the fire cells. The moat is **safety-relevant**
(not just precision) if K1 **dangerously proceeds** (accepts a buried defeater) where K2 blocks —
`Δd ≥ +0.10`. If both are cautious (escalate/block everything), Δd ≈ 0 and the moat, if any, is in
posture precision only — report that honestly.

## Don't let escalation masquerade as surfacing
A model that escalates everything is *safe* but has **not surfaced** the specific defeater. So also
report **committed-correct** (escalate=False AND correct block posture), K2 vs K1: real surfacing is
the stack committing to the right block where raw-docs escalates or proceeds.

## Catalog-completeness audit (built in)
Any coverage **fire** cell where **K2 itself fails the block posture** is a **catalog gap** — the
catalog does not enumerate that defeater — not a model failure. List them; they are the punch list
of defeater types to add to the catalog. Pre-registered so a K2 miss is read as a gap, not noise.

## Frontier caveat (mirrors the gate)
The honest K1 is a **frontier** model reading the docs — that is what a buyer actually does. This
cheap run uses stock `qwen2.5:7b` for K1, which **understates** the baseline and **overstates** the
moat. A stock-7B K1 the stack beats is suggestive; a frontier K1 it still beats is the result that
survives scrutiny. Frontier K1 is deferred-but-named, not silently skipped.

## What each outcome means (read straight, not cross-cushioned)
- **Δp ≥ +0.15, CI excludes 0, Δd ≥ +0.10** → the stack surfaces real, safety-relevant defeaters the
  buyer's model misses. The defensibility result; localized to where NVIDIA and ad-hoc model-reading
  both fail.
- **Δp ≤ +0.05** → a smart model reading the docs already catches these; **no coverage moat** on this
  corpus at this model size. Deflating; report it. (Then the frontier K1 only widens the baseline.)
- **K1.5 ≈ K2 > K1** → surfacing is SIP extraction, not the catalog; **K1 ≈ K1.5 < K2** → it is the
  catalog. Tells which layer earns any coverage win.
