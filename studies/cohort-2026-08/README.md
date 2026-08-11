# Cohort study 2026-08 — what raidex furnishes, per Group-B property

**Pre-registered baseline** for the deep study and the FAccT paper. This is a
record of account, not a summary: `results.json` carries the per-model rows, the
individual standard errors, and every exclusion, so a later reader can recompute
any figure quoted from it rather than trusting a number in prose.

| | |
|---|---|
| Dataset | [`cloudronin/raidex-results`](https://huggingface.co/datasets/cloudronin/raidex-results) |
| Revision | `d459f536b506dc5f82355891db19f599f374a92c` (lastModified 2026-07-18) |
| Measured | 2026-08-10 |
| Scope | 43 models, 427 validation results |

## Re-deriving it

```bash
python studies/cohort-2026-08/measure_cohort.py
```

The revision is pinned in the script, so this reproduces `results.json` or tells
you the cohort moved. A **changed** result is a finding about raidex, not a
fixture to resync — record the new revision as a new study directory rather than
overwriting this one. Offline: `--local-dir <dir>` over a directory of records.

Re-run whenever the cohort grows. Per AGENTS.md §13, a verdict measured on a
corpus that has since been regenerated is not a result.

## Findings

### Furnishing rates

| Property | Rule it feeds | Furnished |
|---|---|---|
| `metricValue` | (the score itself) | 427/427 · 100% |
| `wasGeneratedBy` | W-EP-02 (core) | 427/427 · 100% |
| `hasUncertaintyQuantification` | **W-AL-01 (core)** | **43/427 · 10.1%** |
| `generalizedClaim` | COMPOUND-EV-02 | 43/427 · 10.1% |
| `samplingAccount` | W-EV-GEN-02 | 0/427 · 0% |
| `harnessDeterminismStatement` | W-EV-DET-03 | 0/427 · 0% |
| `nullBaselineStatement` | W-EV-NULL-04 | 0/427 · 0% |
| `claimedCOU` | W-EV-COU-05 | 0/427 · 0% |
| `confoundControlStatement` | W-EV-CAP-06 | 0/427 · 0% |

Coverage: 40 models at 9/9, 3 at 8/9.

### What the two shapes of row mean

**The 10.1% row is the important one.** `bbq` publishes a real
`acc_stderr`; the other eight constituents and the composite publish none. So
core's `W-AL-01` fires on 384 results and **clears on 43** — the assessment
distinguishes a furnisher that reports uncertainty from one that does not,
rather than failing everything and calling it rigor. An assessment that fired
uniformly would be indistinguishable from one that had not read the evidence.

`generalizedClaim` also lands at 43/427 for a different reason: it is set on the
RAI composite only, never on a constituent, so COMPOUND-EV-02 fires once per
model rather than once per result.

**The five zero rows are a specification, not a complaint.** They are precisely
what a raidex constituent would have to carry to clear the Group-B bar. This is
the furnisher/assessor loop of the pack spec's §6a stated as a measurement:
raidex furnishes evidence, the pack assesses sufficiency, and the assessment gaps
say what the next constituent needs. Nothing here says the models are bad or the
benchmarks are wrong; the finding is about the published record.

### Exclusions (3, all in `results.json` with their models)

| Reason | Count |
|---|---|
| `connection-error` | 2 |
| `timeout` | 1 |

An excluded constituent carries `value: null` with a populated `error` and is
**not** emitted as a validation result — a node asserting "measured, score
unknown" would be a fabricated measurement. This is raidex's composite-exclusion
rule visible in the data, and it is what `rai_coverage` counts.

Reasons are **classified, never copied**: the raw `error` is a harness traceback
containing the operator's absolute filesystem paths, and bundles built from these
records get published.

### Standard-error distribution (the DIV-07 tolerance)

n=43 (every `bbq`), normalized to 0–100: **min 1.84, mean 3.35, max 4.08**.

`DIV_TOLERANCE_NORMALIZED = 5.0` sits above the cohort maximum — **holds**. The
constant was first derived from four fixtures and is confirmed here against all
43. A tolerance at or below 4.08 would fire on sampling noise at raidex's own
sample sizes. Note `n_samples` is not constant (108 to 738), so the constant is
anchored to the observed standard-error range, not to a sample size. The script
re-checks this assertion on every run.

## What this study does not do

It does not run the pack. It reports what the furnisher *furnishes*; whether that
is sufficient for a given decision is the assessment's job, and conflating the
two would collapse the furnisher/assessor firewall this whole design rests on.
