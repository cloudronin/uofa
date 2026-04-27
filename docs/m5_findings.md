# M5 findings & M6.2 follow-up backlog

Living document. Two sources feed this:

1. **Mid-run observations** — issues I've identified while watching M5 progress (root causes that wouldn't surface from `outcomes.csv` alone).
2. **Post-M5 analyze** — runbook §1 "Triage decision tree" categories, populated from `coverage/outcomes.csv` + `coverage/summary.csv` + `coverage/index.html` after M5 completes.

Each finding has: severity, fix candidate (prompt vs. spec vs. classifier), and whether it blocks the M5 deliverable or only M6.2.

---

## Mid-run findings (Apr 26 M5 run)

### F1 — W-ON-01 prompt template omits `hasContextOfUse`

- **Severity:** High (causes ~20% gen_invalid rate on the 5 W-ON-01 cells at low+medium subtlety; cells finished but with mostly empty packages)
- **Symptom:** 5 W-ON-01 cells (low+medium × 3 base_cous) accumulated 50 / 46 / 45 / 36 / 26 retries before `max_retries=4` cut them off. Single SHACL violation in every failed file: `Profile: Required fields for the declared profile are missing`. The missing field is **`hasContextOfUse`**.
- **Root cause:** `src/uofa_cli/adversarial/prompts/ontological.py` frames the W-ON-01 weakener as "validation evidence comes from a *different* domain than the CoU." The LLM interprets "domain mismatch" as "leave the CoU out" rather than "include a CoU but with mismatched domain content."
- **Why retries didn't recover:** the runner feeds back the SHACL violation message, but it's too generic ("Required fields for the declared profile are missing") — doesn't pinpoint `hasContextOfUse`. The LLM keeps making the same omission.
- **Fix candidate:** add an explicit "preserve the identity block including hasContextOfUse verbatim — the domain mismatch goes INSIDE the validation evidence, not in the CoU itself" directive to the W-ON-01 user prompt. Same fix pattern that already works in the compound-* templates.
- **Blocks:** M6.2 only. The high gen_invalid rate is itself valid Phase 2 §11 / §13.3 data ("the synthetic generator can't reliably produce W-ON-01 triggers at low/medium subtlety without prompt-template revision").

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
