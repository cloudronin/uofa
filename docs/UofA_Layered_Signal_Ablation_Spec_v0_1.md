# Layered Signal Ablation + Coverage — Spec v0.2 (revised after review)

> Revised from the v0.1 Product Requirements spec after review. Incorporates the five fixes,
> adds **Experiment B (coverage)** as the test that actually bears on UofA defensibility, and
> de-cushions the reads. Extends `harness/bakeoff/`; reuses `score.py` unchanged. **Queued** —
> built after the catalog ablation lands. Curation rows (the raw-artifact renderings) do not
> accelerate.

## Two questions, two experiments — read independently, never cross-cushioned

UofA's value over "the NVIDIA PhysicsNeMo guardrails a buyer already has + a smart model reading
the docs" splits into two **independent** axes. The v0.1 design measured only the first and then
leaned on the second to soften a possibly-flat result. That is reading fit to hope. Measure both;
read each straight; synthesize only from two real results.

- **Experiment A — interpretation lift.** Given a signal NVIDIA already emits, does the UofA
  stack turn it into the right posture better than a threshold or a model on the same signal?
  Lives on the **29/60** cells where a guardrail signal exists. May be flat — if so, say so.
- **Experiment B — coverage lift (the defensibility test).** For the **31/60** defeaters NVIDIA
  emits *no* signal for (data provenance, validation methodology, verification, inheritance),
  does SIP's extraction + the catalog's enumeration *surface* the defeater when a buyer's
  best realistic alternative — a strong model reading the raw artifact — misses it? This is the
  axis that actually decides whether UofA is defensible against "just ask a good LLM."

A flat A means UofA adds no interpretation lift **on the signals NVIDIA emits** — full stop, no
"but coverage." B is then run on its own merits. The honest synthesis ("value is coverage, not
interpretation") is a *conclusion from two straight results*, not a hedge applied to one.

---

# Experiment A — interpretation lift (where the posture-lift lives)

Three stacked layers: NVIDIA guardrails emit raw signals (geometry-OOD percentile, PDE residual
magnitude, ensemble-variance field) → SIP measures them → catalog+model interpret to a posture.
NVIDIA is a **signal source feeding SIP**, not a competitor (no shared metric). Hold model, cells,
output schema, and scorer constant; vary only the interpreter stack.

## The conditions — four, not three (Fix #2: separate SIP from the catalog)

The v0.1 C2→C3 gap bundled SIP-structuring with the catalog, and the catalog is *already* isolated
by the existing ablation (its lift is confidence-to-commit, not danger-catching). Insert the
intermediate condition so the genuinely new layer — SIP — is attributed cleanly.

| Cond | Interpreter sees | Interpreter | New isolation |
|---|---|---|---|
| **C1 — threshold** | raw signals (incl. per-region fields, Fix #3) | multi-signal threshold rule | best *free* baseline |
| **C2 — model/raw** | the same raw signals | stock 7B, no SIP, no catalog | model over threshold |
| **C3 — model/SIP** | SIP-structured measures | stock 7B, **no catalog** (= `catalog_ablated`) | **SIP's structuring lift** |
| **C4 — full stack** | SIP measures + catalog | the existing `full` pipeline | catalog's lift (already known) |

- **C1→C2** = what a model adds over a threshold on raw signals.
- **C2→C3** = **what SIP's structuring adds** over a model reading raw signals — *the new result.*
- **C3→C4** = the catalog's lift, re-measured here (cross-check against the catalog ablation).

C3 literally reuses the catalog ablation's `catalog_ablated` path on the NVIDIA-signal cells, so
this costs one extra condition, not a new harness.

## C1 must be a FAIR baseline — and at the SAME granularity (Fix #3)

A UofA win is meaningless unless C1 is the best simple thing:
- **All three signals**, not one. A competent engineer thresholds on everything available.
- **PhysicsNeMo docs' own defaults** as the start (`warn_pct=99.0`, `reject_pct=99.9` for
  geometry-OOD; analogues for residual/variance).
- Rule → {block, proceed, escalate}: any signal ≥ its reject threshold → block; below all warn →
  proceed; between → escalate (mirrors the stack's escalate, so the escalation axis is fair too).
- **Same signal granularity as the stack.** If the conflicting defeater is a per-region interaction
  and C3/C4 read a per-region *field* while C1 thresholds only a global mean, C3's win is a
  granularity artifact, not interaction-reasoning. Hand C1 the same per-region field and let it
  threshold the **worst region**. Then: C1-with-the-field closing the gap = honest "a threshold on
  the right signal suffices"; C1 *unable* to close it = the stack's win is real interaction value.
- **Pre-register that every conflicting-cell defeater is an interaction of ≥2 signals** (not
  thresholdable at any single granularity). Otherwise the worst-region threshold trivially catches
  it and the experiment has no room to discriminate.

## C1 tuning — docs-defaults for the cheap run (Fix #4)

Tuning C1's thresholds on the same cells it is scored on can **overfit** the baseline → an inflated
"threshold suffices" → a **false null** that wrongly kills the experiment at the cheap gate (the
overfit direction is conservative for a *win* but dangerous for the *deflating result*, which is the
cheap run's actual job to detect). Use docs-default (or held-out-tuned) thresholds for the cheap run
and document them. Reserve cell-tuned C1 for the real run with a held-out split.

## Cheap first, real second — and read the cheap positive narrowly (Fix #5)

1. **Cheap.** Render the **29 mappable cells** in NVIDIA-signal form (percentile / residual /
   variance, conclusion-free, same de-naming discipline as `measures_raw` — a number and a field,
   never "this is OOD"). Build **~6–8 more three-signal conflicting cells** so the conflicting
   subset clears the ≥12 power floor the catalog ablation used. Run C1–C4. A positive cheap result
   means *"interaction-lift is **possible** if real PhysicsNeMo signals conflict this way,"* **not**
   "lift exists" — I hand-author the numbers, so the conflict structure is partly assumed. Worth
   confirming, not confirmed.
2. **Real.** Only if the cheap C2→C3 (and C1→C2) shows lift on conflicting cells: promote to **real
   PhysicsNeMo guardrail outputs** via the two-container demo, on enough cases to score. This is the
   version that survives scrutiny.

## Reading Experiment A — straight

Headline: **C2→C3 (SIP) and C3→C4 (catalog) on the conflicting-signal cells**, grounded posture
axis, **dangerous-error and escalation read together** (a condition that "wins" on danger by
escalating everything has not won — check coverage at the same α).

- **C2 ≈ C3 ≈ C4 on conflicting cells** → on the signals NVIDIA emits, a multi-signal threshold
  reads them as well as the stack. **UofA adds no interpretation lift here.** Report it flat. Do not
  reach for coverage in the same breath — that is Experiment B's job.
- **C2 → C3 gap** → SIP's structuring surfaces interaction the raw-signal model misses; localized,
  real, and the new contribution.
- **C3 → C4 gap** → consistent with the catalog ablation's confidence-to-commit lift; cross-check.
- **Lift only on stark cells** → the stack helps only where a threshold already works; near-null.

---

# Experiment B — coverage lift (the defensibility test)

The 31 cells NVIDIA emits no signal for are not a footnote — they are where UofA's moat, if any,
actually is. The question is **not** the degenerate "stack wins because the baseline is handed
nothing" (trivially pro-UofA, proves nothing). It is the buyer's real question:

> A smart model reading the raw evidence package already flags obvious credibility problems. Does
> SIP's systematic extraction + the catalog's enumeration **surface defeaters that the model reading
> the raw docs does not** — because it does not think to look — and at a rate that justifies the
> stack over "paste the docs into a good LLM"?

## The conditions

| Cond | Interpreter sees | Tests |
|---|---|---|
| **K1 — model/raw-artifact** | the **unstructured** evidence package as prose (model card / validation report containing the defeater, **unflagged**), no SIP fields, no catalog | the buyer's real free alternative |
| **K1.5 — model/SIP** | SIP-extracted structured measures, no catalog | **SIP's extraction/surfacing lift** |
| **K2 — full stack** | SIP measures + catalog enumeration + model (`full`) | extraction + enumeration together |

- **K1 → K2** = the **headline defensibility gap**: does the stack catch coverage defeaters the
  buyer's model-on-raw-docs misses.
- **K1 → K1.5** = how much of that is **SIP extraction** (structuring the artifact surfaces the
  field) vs the catalog naming it (K1.5 → K2).

## The fair baseline — and the frontier caveat (mirrors the gate)

K1 must be the buyer's **best** realistic alternative, or a UofA win is hollow:
- A reasonable generic prompt ("review this surrogate's credibility evidence for use in <COU>; flag
  concerns; recommend a posture"), not a crippled one.
- **The honest K1 is a frontier model reading the docs** — that is what a buyer actually does. A
  stock-7B K1 *understates* the baseline and **overstates** the coverage moat. So, exactly like the
  gate: cheap K1 = stock 7B with the caveat stated explicitly; **the real defensibility number needs
  K1 = frontier**, deferred but named, not silently skipped.

## The real cost — the raw-artifact renderings (curation, no acceleration)

K1 needs each of the 31 defeaters rendered as a **naturalistic, unstructured artifact** (a few
paragraphs of model-card / validation-report prose) that *contains* the defeater without flagging it
— the model has to *find* it. This is distinct from `measures_raw` (still structured fields) and is
the genuine expense of B, the same way corpus curation was for the catalog ablation. Label
provenance external to the tool.

## B doubles as a catalog-completeness audit

If K2 (full stack) *misses* a coverage defeater, the catalog does not enumerate it — a concrete
catalog gap to fill. B's per-cell read therefore yields both the defensibility number and a punch
list of defeater types the catalog should add. Pre-register: a coverage defeater K2 misses is a
catalog gap, not a model failure.

## Reading Experiment B — straight

Grounded posture axis, dangerous-error and escalation together (same discipline).

- **K1 ≈ K2 on coverage cells** → a smart model reading the docs already catches these defeaters.
  **No coverage moat** — the catalog re-derives what the model knows. Deflating; report it.
- **K2 ≫ K1 (K1 dangerously false-OKs, K2 catches)** → the stack surfaces real defeaters the buyer's
  model misses. **This is the defensibility result** — UofA's value is systematic coverage, and it
  is localized to the defeaters NVIDIA and an ad-hoc model both miss.
- **K1.5 ≈ K1 < K2** → surfacing comes from the catalog enumeration, not SIP structuring (or vice
  versa for K1 < K1.5 ≈ K2). Tells you which layer earns the coverage win.

The frontier caveat bounds the strength: a stock-7B K1 that UofA beats is suggestive; a frontier K1
that UofA still beats is the result that survives scrutiny.

---

# Synthesis (only after both run)

Lay A and B side by side, each read straight:
- **A flat, B strong** → UofA's value is **coverage** (systematic surfacing of defeaters), not
  interpretation of signals NVIDIA already emits. A defensible, honestly-narrow position.
- **A strong, B strong** → value on both axes; strongest case.
- **A flat, B flat** → on this corpus, neither interaction-reasoning nor systematic coverage beats
  "NVIDIA signals + a smart model reading the docs." The deflating finding the whole design exists to
  be able to reach — and the one most worth knowing before betting on the stack.

No outcome is cushioned by the other. Each gap is pre-registered before its run.
