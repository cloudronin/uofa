# Live-run verification checklist (A13)

**Status: NOT YET RUN.** Everything under `--raidex-run` was built and tested
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

- [ ] `raidex eval <model-ref> --out <tmp>/results.json` is the real invocation —
      flag names, argument order, and `--out` semantics match the installed CLI.
- [ ] The written `results.json` parses through the **unchanged** Phase 2 adapter
      (`furnishers/raidex.py`). If it needs adapter changes, the "same code path
      as `--raidex <path>`" claim in A13.2 is false and must be corrected.
- [ ] A non-zero exit is surfaced with raidex's own stderr, not swallowed.
- [ ] A partial sweep produces a bundle whose `rai_coverage` says so — no error,
      no silent gaps (A13.4).
- [ ] `--raidex-args` passthrough reaches raidex uninterpreted.

## 2. Preflight honesty (A13.4) — the highest-risk item

The cost/time statement is currently derived from constituent count and sample
sizes. **It has never been checked against a real run.** A preflight that
under-states spend is worse than none: it converts an informed decision into a
false assurance, and the user only finds out mid-sweep.

- [ ] Record predicted vs actual wall-clock, per constituent and total.
- [ ] Record predicted vs actual judge token spend / cost.
- [ ] State the observed error band in this file. If the estimate is out by more
      than it is useful for, either widen it to an honest range or remove the
      number and print only the constituent list and judge config.
- [ ] Confirm the estimate is stated as an estimate, never as a quote.
- [ ] `--yes` skips confirmation; without it, declining actually aborts before
      any provider call is made.

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
