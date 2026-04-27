# M5 findings & M6.2 follow-up backlog

Living document. Two sources feed this:

1. **Mid-run observations** — issues I've identified while watching M5 progress (root causes that wouldn't surface from `outcomes.csv` alone).
2. **Post-M5 analyze** — runbook §1 "Triage decision tree" categories, populated from `coverage/outcomes.csv` + `coverage/summary.csv` + `coverage/index.html` after M5 completes.

Each finding has: severity, fix candidate (prompt vs. spec vs. classifier), and whether it blocks the M5 deliverable or only M6.2.

---

## Mid-run findings (Apr 26 M5 run)

### F1 — Weakener semantics conflict with SHACL profile shapes (NOT a prompt bug)

**Important correction (Apr 27):** I initially diagnosed F1 as a prompt-template bug ("LLM is being told the wrong thing and dropping required fields"). After actually reading the prompt source + the SHACL shapes, **the prompt is doing exactly what it's supposed to do — the bug is a design tension between the weakener semantics and the SHACL shapes**.

#### F1a — W-ON-01 (missing Context of Use)

- **W-ON-01 *is* "the package has no `hasContextOfUse`."** That's the literal weakener definition.
- The W-ON-01 prompt template (`prompts/ontological.py:34-38`) correctly instructs: "Emit `conformsToProfile: ProfileMinimal`. Do NOT emit `hasContextOfUse` anywhere."
- The W-ON-01 prompt comment explicitly assumed: *"Phase 2 confirm_existing for W-ON-01 therefore generates the rare-but-possible Minimal-profile package whose Minimal SHACL allows hasContextOfUse to be absent. The classifier is expected to accept this as the documented W-ON-01 scope."*
- **That assumption is wrong.** Reading `packs/core/shapes/uofa_shacl.ttl:50-55`:
  ```turtle
  uofa:UnitOfAssurance_MinimalBody
    sh:property [
      sh:path uofa:hasContextOfUse ;
      sh:minCount 1 ;       # ProfileMinimal REQUIRES hasContextOfUse
    ] ;
  ```
- Both ProfileMinimal AND ProfileComplete require `hasContextOfUse`. There is no SHACL profile under which a W-ON-01 package can conform.

#### F1b — W-SI-01 (missing signature)

- Same pattern: W-SI-01 *is* "the package has no `signature`" (`prompts/structural.py:28`).
- ProfileMinimal SHACL (`uofa_shacl.ttl:74-79`) requires `signature` with `minCount 1`.
- Same fundamental conflict.

#### What this means for catalog_recall

The runner's SHACL gate categorically prevents generation of W-ON-01 / W-SI-01 packages at any subtlety. Most variants exhausted `max_retries=4` and were marked GEN-INVALID. **Reporting catalog_recall as "0%" or "near-zero" for these patterns would be misleading — the rules never had a chance to fire because no evaluable package was produced.**

Implemented Apr 27: the classifier now distinguishes:
- `recall = "<float>"` — measured, n>0 evaluable rows
- `recall = "not_measurable"` — n=0 evaluable rows but ≥1 GEN-INVALID rows targeting this pattern (F1-class weakeners fall here)
- `recall = ""` — no confirm_existing rows targeting this pattern at all

The reporter's View 1 catalog × subtlety pivot renders these cells as "not measurable" with a dedicated CSS class instead of "0%". See `tests/adversarial/test_classifier.py::test_write_summary_csv_recall_marks_not_measurable_when_only_gen_invalid` and `tests/adversarial/test_reporter.py::test_view1_renders_not_measurable_for_all_gen_invalid_cell` for the pinned behavior.

#### Three real options for resolving F1 in M6.2 / Phase 3

| Option | Description | Effort | Caveat |
|---|---|---|---|
| **A. Accept** | Document "not measurable" as the honest signal. Don't try to test these weakeners until the SHACL/weakener tension is resolved at the design level. | $0, ~30 min docs | Catalog coverage for these 2 patterns becomes a Phase 3 reviewer question, not a Phase 2 metric |
| **B. Fix the runner** | Add a "weakener bypasses SHACL retry-gate" mechanism for weakeners that semantically require omitting required fields. The package gets written; analyze classifies based on rule firings even though SHACL didn't conform. | $15-20 + 2-4h code | Requires careful design — might need a new outcome class `GEN-NON-CONFORMING-BY-DESIGN` to distinguish from GEN-INVALID |
| **C. Loosen SHACL** | Edit `packs/core/shapes/uofa_shacl.ttl` so ProfileMinimal allows these fields to be absent | $15-20 + 30 min | Alters the core schema; affects EVERY user of the pack, not just adversarial. Probably not the right answer. |

**Decision (Apr 27): Option A for now.** Continued with M5 analyze; documented the design tension here. M6.2 / Phase 3 will revisit with proper time + design pass.

#### Other weakeners potentially affected

The required ProfileMinimal fields are: `bindsRequirement`, `hasContextOfUse`, `hasValidationResult`, `generatedAtTime`, `hash`, `signature`, `hasDecisionRecord`. ProfileComplete additionally requires `bindsModel`, `bindsDataset`, `hasCredibilityFactor`. Any weakener whose semantic requires omitting one of these fields will hit the same F1-class issue. Worth auditing the full weakener catalog during M6.2.

#### Side note: SHACL retry-feedback message is too generic

The runner appends the SHACL violation message to the retry prompt. For F1-class failures the message is "Required fields for the declared profile are missing" — without naming *which* field. **Even outside F1**, this is a worth-fixing usability issue: improving `shacl_friendly.py`'s ProfileShape violation translation to name the missing fields would make retries actually useful for the LLM. M6.2 candidate (separate from the F1 design-tension question above).

### F2 — Paraphrase variant `p2` triggers Anthropic safety-filter refusal

- **Severity:** Medium (only affects the M6.2 paraphrasing battery, not M5)
- **Symptom:** w-ar-05_p2 spec saw all variants return Anthropic `stop_reason: refusal` with `content: []`. Identical at parallel=1 and parallel=3, so it's NOT a thread-safety bug; it's content-policy.
- **Root cause:** `src/uofa_cli/adversarial/prompts/paraphrase.py::_SUBSTITUTIONS_P2` includes substitutions like `"Plausible on a quick read." → "Reads as plausible at first glance."` that, in combination, push the prompt across Anthropic's safety threshold for "deceptive content generation" requests.
- **Fix candidate:** soften p2 substitutions so the prompt stays tonally close to p0/p1 but still varies wording. Specifically, the "Plausible / Reads as plausible at first glance" pair is the most likely offender — revert that one and most others should pass.
- **Alternative:** drop p2 entirely from the paraphrasing battery; ship M6.2 with just p0+p1.
- **Blocks:** M6.2 only. M5 doesn't include paraphrasing.

### F3 — `BASELINE_FIRINGS` & baseline subtraction (already fixed)

- **Severity:** Was high — caused systematic COV-MISS false negatives.
- **Status:** Fixed in commit `5698cc1`. Documented here for the post-M5 review packet readers' context.
- **Note for Phase 3 reviewers:** any references to `baseline_firings_count` in archived smoke-output CSVs (e.g., `out/.../SMOKE/`) predate the fix and should be ignored.

### F4 — `GEN-INVALID` denominator inflation (already fixed)

- **Severity:** Was medium — would have deflated all View 3 metrics by the gen-failure rate.
- **Status:** Fixed in commit `9554b34`. Recall, precision, and gap-probe-miss-rate now correctly exclude `GEN-INVALID` rows from their denominators.
- **Note for Phase 3 reviewers:** the M5 catalog recall in the final report is the truthful version (evaluable rows only).

### F6 — `--max-cost` accounting double-counts resume-skipped cells

- **Severity:** Medium (caused a spurious M5 halt during the second resume; harmless to data, just bookkeeping)
- **Symptom:** Resumed M5 with `--max-cost 100` halted at 70 cells with $101 reported "cost", but 0 of those 70 cells actually issued LLM calls — they were all `--resume`-skipped from prior runs. The runner's `accumulated_cost` sums every cell's `estimated_cost_usd` (whether skipped or freshly run), and the cap check halts based on the combined sum.
- **Root cause:** `src/uofa_cli/adversarial/runner.py::run_batch` accumulates cost from both newly-processed and resume-skipped cells:
  ```python
  res = _process_spec(args, cell, out_root, args.resume)
  accumulated_cost += res.estimated_cost_usd  # includes prior cost on skip
  ```
  This is meaningful for "total cost the manifest reports" but wrong for "how much will I spend on THIS resume."
- **Fix candidate:** track `accumulated_cost_this_run` separately for the cap check (only summing actually-processed cells), while still preserving `accumulated_cost` for the manifest's cumulative figure.
- **Workaround used during M5:** bump `--max-cost` to effectively-unlimited (`500`) for the resume; the actual incremental spend is much smaller than the cap, so this is safe.
- **Blocks:** M6.2 only. Doesn't affect M5 data integrity, just the cap-halt UX during resume.

### F7 — `analyze` is fully sequential; parallelize for ~5× speedup

- **Severity:** Low (UX improvement, no data-quality impact)
- **Symptom:** Analyzing the M5 batch (4,601 packages) takes ~5 hours wall-clock. Live observation during Apr 27 analyze: at any given moment exactly 1 `uofa-weakener-engine` JVM is running. Each `uofa rules` call cold-starts a fresh JVM (~2-3s) before parsing + rule evaluation; all per-package calls are sequential.
- **Root cause:** `src/uofa_cli/adversarial/classifier.py::_scan_outcomes` is a plain nested `for spec: for variant: _run_rules_on_package(path)` loop. No `ThreadPoolExecutor`, no `multiprocessing` — one package at a time.
- **Fix candidate:** mirror the runner's `--parallel` design. Wrap the per-package Jena calls in a `ThreadPoolExecutor` pool. Each `uofa rules` invocation spawns its own JVM subprocess, so there is **no shared state** to worry about — thread-safety is essentially free at the analyzer level.
  ```python
  # Sketch — classifier.py
  with ThreadPoolExecutor(max_workers=parallel) as pool:
      futures = {pool.submit(_run_rules_on_package, p, pack=pack): (spec, variant)
                 for (spec, variant, p) in package_iter}
      for fut in as_completed(futures):
          firings, timings = fut.result()
          # ... existing classification + accumulation
  ```
- **Estimated impact:** at parallel=5 → ~1 h wall-clock for M5 instead of ~5 h. For Phase 3-scale datasets the speedup compounds. Comparable to the runner's parallel=5 boost we just verified.
- **Caveats:**
  - The analyze CLI would need a `--parallel` flag (defaulting to 1 for parity with current behavior).
  - D2 timing instrumentation already captures `total_eval_ms` per package, so the perf appendix would just see correlated wall-clocks across the threads — no metric distortion.
  - System memory: 5 × ~500 MB JVM = ~2.5 GB peak, well within typical Mac/Linux dev box budgets.
- **Blocks:** M6.2 only. Does NOT affect any M5 data integrity. Pure throughput improvement.

### F5 — pyshacl/rdflib stream-consume bug (already fixed)

- **Severity:** Was high — would have caused random false-negative SHACL failures throughout M5.
- **Status:** Fixed in commit `8aa63de` (pre-parse data graph in `_load_data_graph`).
- **Note for Phase 3 reviewers:** if the final M5 outcomes have unusually low gen_invalid rates compared to historical smokes, this fix is why.

---

## Anthropic API stability (informational)

Mid-run accumulation, not a "fix me" finding — just observability:

| Error | Count over 14h | Notes |
|---|---|---|
| `Server disconnected without sending a response` | 3 | Transient, recovered on retry |
| `Internal server error` (HTTP 500) | 1 | Recovered on retry |
| `Unparseable JSON` (truncated mid-string) | 1 | Single occurrence; model output cut off at char ~27k |

All recovered through the runner's per-variant retry loop. No spec-level impact.

---

## Post-M5 findings (Apr 27 analyze)

> _Populated from `out/adversarial/phase2/2026-04-26/coverage/{outcomes,summary,matrix}.csv` and the rendered `index.html`._

### Headline outcome distribution (n = 4,605 rows)

| Battery | n | Outcome distribution |
|---|---|---|
| confirm_existing | 4,005 | **2,661 HIT-PLUS / 965 WRONG / 379 GEN-INVALID** (recall = 73.4%) |
| gap_probe | 330 | 0 MISS / 329 WRONG / 1 GEN-INVALID (miss rate = 0%) |
| interaction | 90 | 90 HIT-PLUS / 0 misses (target fires 100%) |
| negative_controls | 180 | **176 CLEAN-WRONG / 4 GEN-INVALID** (precision = 0%, FPR = 100%) |

Notably absent: **0 COV-HIT** (target alone) and **0 COV-MISS** (zero rules firing). Every package triggered *something*; when the target fires, bystanders fire too.

### View 3 metrics

| Metric | Value | Threshold (runbook §1) | Status |
|---|---|---|---|
| Catalog recall (HIT + HIT+) | **73.4%** | <70% triggers triage | ⚠ borderline (3.4% above threshold) |
| Catalog precision (1 − FPR) | **0.0%** | <90% triggers triage | ✗ **major finding — worst-case** |
| Gap-probe MISS rate | **0.0%** | none documented; informational | informational only |

### Two big Phase 2 takeaways

#### Finding M5-A: Catalog is systemically over-eager (FPR = 100%)

Every clean negative-control package (176 of 180 evaluable, the other 4 GEN-INVALID) triggered at least one rule firing. The catalog's rules are not specific enough — they fire on packages that should be quiet.

This is the most actionable Phase 3 reviewer signal in the entire M5 dataset. Worth detailed §6.7-style investigation: inspect a sample of `COV-CLEAN-WRONG` rows in `outcomes.csv`, see *which* rules fired, and decide whether each is (a) a too-permissive rule pattern, (b) a synthetic-generator artifact (NC packages too "rich" because LLMs over-produce structure), or (c) a legitimate concern the rule correctly detected (FPR = false positive only if the rule fires on something genuinely clean).

#### Finding M5-B: 0 COV-HIT, 100% HIT-PLUS — high inter-rule correlation

When a target rule fires, other rules fire too. Across 2,661 HIT-PLUS confirm_existing rows, ZERO had only the target firing. The catalog has strong inter-rule correlation — possibly because the synthetic packages are structurally complex enough that multiple rules pattern-match simultaneously, or because the rules themselves overlap semantically.

Implication: the "rule independence" assumption that underlies simple recall/precision metrics is broken. Phase 3 should consider per-rule precision (which rule contributed to which firing) rather than just package-level outcome class.

### Gen-invalid rate by battery

| Battery | n_total | gen_invalid | rate | vs runbook threshold (>5%) |
|---|---|---|---|---|
| confirm_existing | 4,005 | 379 | **9.5%** | ⚠ **above threshold** |
| gap_probe | 330 | 1 | 0.3% | ✓ |
| interaction | 90 | 0 | 0.0% | ✓ |
| negative_controls | 180 | 4 | 2.2% | ✓ |

The confirm_existing 9.5% is **concentrated almost entirely on F1-class cells** (W-ON-01 + W-SI-01 — the design-tension weakeners that semantically force omission of SHACL-required fields). Excluding F1 cells, the residual rate is well under threshold. The "not_measurable" sentinel in summary.csv flags these patterns specifically.

### Catalog precision = 0% — what fired on the clean controls?

_Per-rule breakdown TODO: walk `outcomes.csv` for `outcome_class == "COV-CLEAN-WRONG"` rows, tabulate `rules_fired` to identify which catalog rules are the FPR drivers. Highest-firing rules are the prime candidates for §13.3 catalog audit._

### COU disparity (D1)

Per `summary.csv`: per-pattern `recall_morrison_cou1` / `_cou2` / `_nagaraja` columns are populated. `cou_dependent_flag` flags patterns with ≥30% recall disparity across COUs. Top COU-dependent rules to surface in Phase 3 reviewer sessions are listed in summary.csv.

### Section §6.7 candidates (gap_probe COV-MISS)

**0 COV-MISS rows on gap_probe** — every gap_probe variant fired at least one rule (classified as COV-WRONG since gap_probe specs have target_weakener=null, so any firing counts as "wrong-target"). This means the catalog is *covering* the literature taxonomy gaps in some way — but probably with non-targeted rules.

Triage approach: walk `outcomes.csv` for `coverage_intent == "gap_probe"` rows, group by `source_taxonomy`, tabulate `rules_fired`. For each (taxonomy, rule_set) pair, Phase 3 reviewers assess: (a) is the firing rule semantically correct for this gap? (b) if not, is it a candidate for a new rule that better captures the literature concept?

D3 prep-review CLI generates per-spec reviewer packets for this triage. Run when ready:

```bash
uofa adversarial prep-review \
  --outcomes out/adversarial/phase2/2026-04-26/coverage/outcomes.csv \
  --output   out/adversarial/phase2/2026-04-26/review_packets/ \
  --max-cases 50
```

---

## Items deferred to Phase 3

These are explicitly out of scope for M6.2 cleanup; they're Phase 3 reviewer-recruitment / catalog-refinement work:

- New rules to add to the catalog based on §6.7 candidates
- Reviewer recruitment + Upwork outreach
- Java-side per-rule timing instrumentation (D2 fallback persists)
- Cross-pack rule semantics (CP-1..CP-10 may surface NASA-specific patterns worth elevating to core)

---

## Document maintenance

- Update findings in real-time as new ones surface (mid-run **or** during analyze triage).
- Each fix that lands gets its commit hash stamped here.
- After all M6.2 cleanup is done, consolidate into a Phase 3 handoff section and tag.
