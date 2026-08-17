# INV-16 — decomposing the 0% → 97.1% NC clean-rate trajectory

Status: **CLOSED** — the split is measurable, and it is measured
Date: 2026-08-17
Feeds: Ch3's specificity narrative (P25-E), GATE-H3's FP clause, the limitations section
Follows: the M5 re-analysis (`98959943`) and its adjudication

## The question

The manuscript's specificity narrative is the trajectory **0% → 97.1% NC clean**,
attributed to a metric-gated refinement loop — `PHASE2_5_STATUS_REPORT.md:13`, *"a
refinement loop drove the catalog's negative-control clean rate from 0% (M5
baseline) → 97.1%."*

Two things changed across that interval: the **rules** were refined over 15
iterations, and the **negative-control corpus was regenerated**. The trajectory
credits the first. This measures how much each contributed.

## Method

Hold the corpus fixed and vary the catalog version. The M5 NC corpus
(`dev/build/adversarial/phase2/2026-04-26`, 179 packages, 176 evaluable) is
unchanged since 2026-04-26 and its v0.5.7 clean rate is committed. Re-classifying it
at v0.5.15.1 isolates the rule-refinement component with nothing else moving.

## Result — the split

| | M5 corpus, unpatched | v0.5.12 hybrid | regenerated corpus |
|---|---|---|---|
| **v0.5.7** | **0/176 = 0.0%** | **0/148 = 0.0%** | **0/171 = 0.0%** |
| **v0.5.15.1** | **8/176 = 4.5%** | — | **166/171 = 97.1%** |

**Rule refinement, corpus held fixed: 0.0% → 4.5%, a gain of 4.5 points.**
**Corpus regeneration, catalog held fixed at v0.5.7: 0.0% → 0.0%. No gain at all.**
**The 97.1% exists in exactly one cell of four.**

> **CORRECTION, 2026-08-17.** This section first read *"The remaining 92.6 points
> travel with the corpus,"* and the fourth cell **falsifies it**. They travel with
> neither factor: the regenerated holdout scores **0.0%** against the old catalog.
> The wrong sentence reached for an additive split that the *"not additive"*
> subsection below already disclaimed, and the measurement sided with the
> subsection. Recorded rather than edited away, per
> [the pre-declaration](../../studies/phase2_5a/FOURTH-CELL-PREDECLARATION.md), whose
> own prediction for the hybrid cell held. **Both reproduction cells reproduced their
> committed figures exactly** — 0/176 and 166/171, denominators included — so the
> table is not distorted by the four-month code gap.

### Per-rule, both endpoints on the same corpus

The M5 baseline column is the project's own, from
`v0.5.12-w-con-fixes/v0512_summary.md:23-35`. The action column is that file's
recorded classification of each fix, written at the time it was made.

| Rule | M5 @ v0.5.7 | M5 @ v0.5.15.1 | Δ | action, as recorded in 2026-04 |
|---|---|---|---|---|
| W-EP-01 | 100.0% | **0.0%** | −100.0 | predicate guard (v0.5.8) |
| W-AL-02 | 100.0% | **0.0%** | −100.0 | schema-aligned predicate (v0.5.9) |
| W-CON-01 | 19.9% | **0.0%** | −19.9 | predicate guard (v0.5.12) |
| W-AR-01 | 1.1% | **0.0%** | −1.1 | predicate guard (v0.5.12) |
| W-ON-02 | 89.8% | **89.8%** | **−0.0** | **corpus regen (v0.5.10)** |
| W-AR-02 | 23.9% | **23.9%** | **−0.0** | **corpus regen (v0.5.11)**, + schema |
| W-CON-04 | 17.6% | **17.6%** | **+0.0** | **corpus regen (v0.5.12)** |
| W-EP-04 | 2.8% | 2.8% | 0 | audit only — legitimate detections |
| COMPOUND-01 | 89.8% | 20.5% | −69.3 | chain auto-fix (derivative) |
| COMPOUND-03 | 79.5% | 23.3% | −56.2 | chain auto-fix (derivative) |

**Every rule the record labels a predicate fix went to zero. Every rule it labels
corpus regen is unchanged to the decimal.** The 2026-04 labels predict the
2026-08 fixed-corpus behaviour exactly, with no exceptions.

### Confirmed a second way, denominator-free

The three regeneration tools live in a directory named `corpus_regen` and each
states the number of packages it patched. Raw firing counts at v0.5.15.1 on the
unpatched corpus:

| Tool | states | measured now |
|---|---|---|
| `regen_nc_envelope.py` (W-ON-02) | "158 minimal NC packages" | **158** |
| `regen_nc_offset_rationale.py` (W-AR-02) | "42 NCs" | **42** |
| `regen_nc_consistency.py` (W-CON-04) | "31 NCs" | **31** |

Three independent exact matches, on counts rather than rates, so no denominator
convention is doing the work. The firing sets these tools were built to remove are
the firing sets still present.

### Why four genuine rule fixes buy only 4.5 points

A package is clean only if **no** rule fires. W-ON-02 alone still fires on 158 of
176, so the ceiling for rule refinement on this corpus is **10.2%** (18/176) no
matter how many other rules are fixed. Of those 18, eight are clean and ten are
caught by W-AR-02 (6), COMPOUND-03 (6) and W-CON-04 (4). The four rules that were
genuinely fixed were not the ones holding the rate down.

## What this does and does not establish

**The refinement is real.** Four rules went from firing on up to 100% of clean
packages to firing on none, and they stayed at zero when re-measured four months
later on the corpus that motivated them. That is a working metric-gated loop and the
narrative is entitled to it.

**The components are not additive, and neither is sufficient — now measured, not
inferred.** Corpus regeneration alone leaves **W-EP-01 firing on 171/171 = 100%** of
the regenerated holdout at v0.5.7; no regeneration tool ever targeted it, because it
was closed by the v0.5.8 predicate guard. Rule refinement alone caps at 10.2%,
because W-ON-02 still fires on 158/176 of M5 and it was never rule-fixed. **The
97.1% required both**, and the reason is symmetric: **each axis is blocked by a rule
that only the other axis fixes.** This is a decomposition of attribution, not of
variance, and the parts do not sum because they are not independent — the gain is
interactive, and 0 + 4.5 does not approach 97.1 from either side.

**The primary record was honest; the rollup lost the distinction.** `v0512_summary.md`
labels each fix "predicate tighten" or "corpus regen" in its status column, states
`"v0.5.12 mixes two patterns in one commit"`, and names the corpus-quality
diagnosis outright: *"rule predicate is structurally correct, NC corpus quality is
the gap."* The information was recorded at the point of decision and dropped on the
way to the summary line. The correction belongs in the rollup, not in the archive.

**The project already drew the line the ruling draws.** `regen_nc_consistency.py`
records that W-CON-01 and W-AR-01 were *"initially scoped to corpus regen"* and were
instead fixed by editing the rule, because *"injecting placeholder values would
violate the factor's stated semantics."* The judgment "is this stub substantively
meaningful?" was made case by case and written down. The limitation is not that the
judgment was skipped — it is that **a presence-checking rule cannot make that
judgment itself**, so nothing in the pipeline enforces it.

## The named limitation

A rule that checks for the presence of a property cannot distinguish a real
operating envelope from an empty one. The regenerated controls satisfy W-ON-02 with
stubs the source calls *"structurally well-formed, not substantively meaningful."*
The rule is satisfied; the evidence is not.

This is the [W-AR-05 case](INV-15-m5-scale-and-phase3-gap-probes.md) from the
opposite direction. There, real evidence was invisible because it was not structural.
Here, non-evidence is visible and passes because it is. **Structural capture is
necessary but not sufficient**; substantive sufficiency checking is future work, and
the MECHANICAL/JUDGMENT partition already carries the vocabulary for the distinction.

Two independent examples of one limitation, both from committed records, neither
constructed for the argument.

## Recommended statement of the trajectory

> The negative-control clean rate rose from 0% to 97.1% across Phase 2.5. Both the
> catalog and the negative-control corpus changed over that interval, and measuring
> all four combinations shows the gain belongs to neither alone. Holding the corpus
> fixed, rule refinement moves the rate from 0% to 4.5%. Holding the catalog fixed at
> the old version, the regenerated corpus scores 0%. The 97.1% appears only where
> both are present, because each axis is blocked by a rule the other one fixes:
> W-EP-01 fires on every negative control at the old catalog whatever the corpus, and
> W-ON-02 fires on 90% of the old corpus whatever the catalog. The specificity result
> is real and it is joint.

## Coverage statement

**Measured.** All 176 evaluable M5 NC rows re-classified at v0.5.15.1 (`m5_results.json`,
`98959943`), per-rule firing counted from `rules_fired`. M5 baseline column read from
`v0512_summary.md:23-35`; action labels from the same file's status column and
`:89-104`. Tool package counts read from the docstrings of all three files in
`dev/tools/phase2_5/corpus_regen/`. Ceiling arithmetic computed over the 18 rows
where W-ON-02 is silent.

**Also measured, 2026-08-17 (`run_fourth_cell.py`).** All three NC corpora
re-classified against the tag-`v0.5.7` catalog through the `--rules` override with
current code, plus the regenerated holdout re-classified at v0.5.15.1 as a second
reproduction check. Both reproduction cells matched their committed figures exactly,
headline and denominator, and cell A additionally reproduced all ten per-rule values
of the 2026-04 baseline table. This closed the 2×2 and falsified one sentence of the
original analysis, corrected above.

**Not measured.**
- **The hybrid corpus is no longer schema-valid.** Cell C's denominator is 148 of
  180: its inserted `hasSensitivityAnalysis` stubs are the inline-object form current
  SHACL rejects (the D2 mismatch), so 31 packages read non-conformant today. The 0.0%
  holds on every evaluable row, but no other figure should be quoted from that corpus
  without the note.
- **Intermediate catalog versions were not swept.** Only v0.5.7 and v0.5.15.1 were
  measured; where between them the 4.5 points arrive is unmeasured, and the per-rule
  table's midpoints come from the 2026-04 record rather than from this run.
- **Denominator conventions differ between sources.** `v0512_summary.md:23` states
  "/180 NC total"; the evidence chain at `holdout_v0515_summary.md:106-116` states
  0/176. This analysis uses 176 evaluable, matching the chain. Percentages agree to
  rounding under either; the three exact count matches (158/42/31) do not depend on
  the choice.
- **The 97.1% itself was not re-derived**, only cited. It is 166/171 validated of a
  180-package holdout.
- **COMPOUND-01/03 are derivative** and their deltas are not independent evidence;
  they move with their inputs and are shown for completeness.
- **Whether the regenerated stubs would satisfy a human reviewer** is unassessed. The
  limitation above is that the rule cannot tell; it is not a finding that the stubs
  are inadequate as evidence. That would need a reader study.
