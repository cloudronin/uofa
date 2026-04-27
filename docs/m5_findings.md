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

## Post-M5 findings (populated after analyze runs)

> _This section will be filled in by post-M5 triage per `docs/phase2_runbook.md` §1. Categories below mirror the runbook's triage decision tree._

### Gen-invalid rate by battery

- _Pending M5 completion + analyze._
- Threshold: >5% on any battery is a triage trigger.
- Expected per-battery rough rates based on mid-run data: confirm_existing 5–10% (concentrated on W-ON-01), gap_probe ?, NC ?, interaction ?.

### Catalog recall (View 3)

- _Pending._
- Threshold: <70% on any pattern is worth investigating.
- Per-pattern rates already available in summary.csv after analyze.

### Catalog precision (View 3)

- _Pending._
- Threshold: <90% precision (i.e., FPR > 10% on negative_controls) is a triage trigger.
- Smoke evidence: NC precision was 0% on a 3-package sample — suggests synthetic generator over-produces structurally rich packages even when prompted as "clean controls."

### COU disparity (D1, summary.csv)

- _Pending._
- Threshold: any pattern with `cou_dependent_flag=True` (≥30% disparity across base_cous) is a finding.
- Mid-run not yet observable since per-COU columns require all 3 base_cous to have data per pattern.

### Section §6.7 candidates

- _Pending._
- These are gap_probe COV-MISS rows that look like real catalog gaps (vs noise).
- D3 reviewer prep packets enumerate these for Phase 3 reviewers.

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
