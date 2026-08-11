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
