# Live-run verification checklist (A13)

**Status: PARTIALLY VERIFIED 2026-08-11** against raidex 0.1.4 installed locally,
using `--dry-run` and `--offline` so no provider call was made. Section 1 and the
preflight are now verified; everything requiring real inference and a judge key
is still open. See Results at the bottom.

**Originally: NOT YET RUN.** Everything under `--raidex-run` was built and tested
against a **stubbed subprocess**. The orchestration, provenance stamping,
preflight arithmetic, and flag handling are unit-tested; the *behaviour of the
real `raidex eval`* is not. This checklist is what a live run has to confirm
before A13 can be called verified.

Needs a machine with `pip install uofa[raidex]`, provider API keys, and a judge
configured. Record results by appending a dated section at the bottom — do not
edit the checklist to match what happened.

Why a checklist rather than a test: these are the claims that a mock cannot
falsify, because the mock is written from the same understanding as the code.

---

## 1. The subprocess contract (A13.2)

- [x] **FAILED AS ORIGINALLY WRITTEN, now fixed.** The implementation used
      `raidex eval <model-ref> --out <path>`. raidex 0.1.4 takes `--model` as a
      **required named flag** (not positional) and `--output` (not `--out`), so
      every real invocation would have errored. The stubbed test passed because a
      stub that ignores argv cannot falsify argv. This is the single clearest
      argument for this checklist existing.
- [x] The written `results.json` parses through the **unchanged** Phase 2 adapter.
      Verified on a real `--offline` run: no adapter change was needed, so
      A13.2's "same code path as `--raidex <path>`" holds.
- [x] A non-zero exit is surfaced with raidex's own stderr, not swallowed.
- [x] A partial/failed sweep produces `rai_coverage` saying so. **This exposed a
      second defect:** a sweep where every constituent errors yields
      `rai_coverage "0/9"` and zero usable nodes, and the code reported success —
      making the readout say *"no reported evaluation to assess"*, which is a
      materially more reassuring claim than *"the sweep failed"*. Now a distinct
      state (`attempted-empty`) with its own sentence.
- [ ] `--raidex-args` passthrough reaches raidex uninterpreted (exercised with
      `--offline --limit 2`; not yet with a flag that changes results).

## 2. Preflight honesty (A13.4) — the highest-risk item

**Resolved differently than planned.** UofA no longer estimates at all: raidex
ships `--dry-run`, which prints a per-constituent cost estimate and the coverage
that will result from any skipped judges. The preflight calls it and relays the
output. Asking the furnisher beats a second estimator that would drift from the
thing it estimates, and it removes the failure mode this item was written about.

- [x] Preflight shows raidex's own per-constituent estimate (verified:
      `openai/gpt-4o-mini --tier A+B` → $2.39 total, coverage 6/9 with no judge).
- [x] Stated as an estimate, never a quote. Time is explicitly not estimated.
- [x] Unreachable dry run prints UNKNOWN and says proceeding means agreeing to an
      unbounded spend. It never substitutes a guess.
- [ ] Record raidex's estimate vs actual spend on a real sweep — still open, and
      still the item that needs money to answer.
- [ ] `--raidex-yes` skips confirmation; without it, declining aborts before any
      provider call is made.

## 3. Provenance: `furnished-run` (A13.3)

- [ ] Bundle carries `furnisherVersion` = the installed raidex package version
      **and** the `backend_version` from the output. Both, not either.
- [ ] Invocation timestamp and the content hash of the raw `results.json` are
      recorded, and the raw output is retained in the bundle's evidence store.
- [ ] Fields from a live run stamp `furnished-run`; `--raidex-hub` fields stamp
      `extracted` with their A9.1 source pin. A reader can tell which.
- [ ] Card section [3] header reads "furnished by raidex vX.Y (live run, <date>)"
      and not the published-dataset wording.

## 4. No severity discount for freshness (A13.2)

- [ ] A live run of a model with no null baseline still trips **W-EV-NULL-04** at
      the same severity as the published-dataset path.
- [ ] W-EV-DET-03, W-EV-GEN-02, W-EV-CAP-06 likewise.
- [ ] Diff the firings from `--raidex-run` against `--raidex-hub` for the same
      model: the pattern set should differ only where the underlying evidence
      differs, never because the run was live.

Freshness is not sufficiency. If a live run ever produces fewer weakeners for the
same evidence, the firewall has leaked.

## 5. Local and private models (A13.5)

- [ ] `--raidex-run --card` on a local checkpoint emits bundle + card.json +
      card.html to the output directory.
- [ ] **Nothing leaves the machine** beyond the provider calls raidex itself
      makes. Verify with a network monitor, not by reading the code — no
      telemetry, no phone-home, no uofa.net interaction.
- [ ] `uofa verify` works offline on the resulting bundle.
- [ ] **Investigation item (A13.5):** what checkpoint identity does raidex
      already capture for local models? Reuse it for `sourcePin` rather than
      inventing a parallel scheme. Record the answer here.

## 6. Flag exclusivity and failure modes

- [ ] `--raidex-run` with `--raidex` or `--raidex-hub` fails clearly rather than
      silently preferring one.
- [ ] With raidex not installed, `--raidex-run` fails with the
      `pip install uofa[raidex]` hint while `--raidex <path>` and `--raidex-hub`
      keep working.
- [ ] Interrupting mid-sweep leaves no partial bundle presented as complete.

## 7. End-to-end (the A13.7.2 case, live)

- [ ] Local model, live run, **no model card**: section [1] is an honest no-card
      readout, section [3] is populated. Running benchmarks does not document a
      model, and the readout must not imply otherwise.

---

## Results

_Append a dated section per verification run. Include the machine, raidex
version, models swept, and any checklist item that failed. A failed item is a
finding to record, not a checklist line to soften._

### 2026-08-11 — first paid run (TogetherAI)

Machine: darwin, raidex 0.1.4, litellm pricing available for the target.
Model: `together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo`, judge: same model.

**Run 1 — unbounded tier A. ABORTED, and the abort is the finding.**

Estimate $10.65 across 7 benchmarks. Started, and `bbq` alone turned out to be
**58,492 prompts at ~2.4/sec — ETA 5h23m for one benchmark of seven.** Aborted at
3,484 prompts (~$0.18 spent).

The cost estimate was not the problem. **Nothing estimated the time**, and the
preflight said so honestly ("Time is not estimated") without that being
sufficient: an operator approves a $10.65 sweep and learns mid-run it is a
day-long job. A13.4's own sentence — "the command must not discover this for the
user mid-run" — describes exactly what happened. **Cost alone does not discharge
A13.4.**

Compounding it: every published cohort record used `--limit` (`bbq n_samples` of
150 and 300). The unbounded run did not match how the cohort was produced, and
that was visible in fixtures already analysed.

**Fix (Phase 6):** print prompt counts beside dollars. raidex already tracks
`full_n` per benchmark for `token_cost`; surfacing it would have made "58,492 for
bbq" visible before agreeing. Upstream: raidex could print counts in `--dry-run`.

**Run 2 — `--limit 150`, matching the cohort. COMPLETED.**

| | |
|---|---|
| Estimated | $0.74, 7 benchmarks |
| Wall clock | **17m (1019s)** |
| Coverage | **7/9** (advglue, confaide are tier B) |
| Failures | 0 across all 7 |
| Result | `rai_score 65.8`, badge `independent` |

- [x] Judge path exercised: simpleqa / strongreject / xstest all ran with a
      Together-hosted judge and reported `judge_model` in the record.
- [x] Adapter ingests a fresh 0.1.4 record unchanged: 8 nodes (7 constituents +
      composite), 0 excluded.
- [x] **Discrimination holds on new data**: `bbq` is again the only constituent
      furnishing an uncertainty, so W-AL-01 clears on 1 of 8 and fires on 7. This
      was not an artifact of the published cohort.
- [ ] **Actual dollars still unmeasured.** raidex records `n_samples`/`n_failed`
      but no token spend, so estimate-vs-actual needs the provider dashboard.
      This is a gap in the record, not in the run.

**Finding — 0.1.4 furnishes more than the published cohort, and the adapter
discards it.** A fresh record carries a `provenance` block the 43 published
records lack:

- `provenance.datasets` — 7 benchmark pins with revision hashes
  (`bbq → oskarvanderwal/bbq @ ab00114b0f…`). The eval *inputs* are pinned even
  though the *subject* is not.
- `provenance.sampling` — `limit`, `sample_exempt`, `concurrency`, `num_retries`,
  `timeout`, `max_failure_rate`. **This is a sampling account**, which is what
  W-EV-GEN-02 tests for.

So raidex 0.1.4 already supplies material that would clear or partially clear two
of the five zero rows in `studies/cohort-2026-08/` — on fresh runs only. Ingesting
it is a Phase 4/6 item, and it is the furnisher/assessor loop of §6a observed
closing rather than argued.

**Upstream suggestions for raidex** — all three filed 2026-08-11
([#1](https://github.com/cloudronin/raidex/issues/1),
[#2](https://github.com/cloudronin/raidex/issues/2),
[#3](https://github.com/cloudronin/raidex/issues/3)); each cheap, each closing a
weakener on grounds already true:

1. Persist `generation_kwargs`. lm-eval logs `temperature: 0.0, do_sample: False`
   at run time; none reaches the record, so W-EV-DET-03 fires across all 427
   cohort results for want of *reporting* determinism, not for want of it.
2. `--dry-run` reports `TOTAL $0.00` when litellm has no pricing, because litellm
   returns `(0, 0)` for an unknown model rather than raising — so the no-pricing
   fallback in `core/cost.py` is unreachable. Observed on
   `together_ai/meta-llama/Llama-3.2-3B-Instruct-Turbo`.
3. Print prompt counts in `--dry-run` alongside cost.
