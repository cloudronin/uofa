# Phase 3 Stage 4 — adjudication and agreement report

Catalog **v0.5.15.1** (frozen); corpus **2026-04-26**. Adjudication completed and
readouts run **2026-08-19**. Re-derive every figure below with

```bash
PYTHONPATH=src python studies/phase3_stage4/rederive_stage4.py
```

which writes `stage4_readouts.json` and exits non-zero if any structural
invariant fails. Corpus-wide κ comes from `uofa adversarial adjudicate` (command
in *Method notes*); its output is `dev/build/adversarial/phase3/adjudication/`.
All inputs are force-tracked under `dev/build/adversarial/` (`.gitignore:41-43`),
so this runs from a clean clone.

---

## The finding

**The spot-check override gate fails, and it fails on the stratum nobody was
watching.**

The author adjudicated 71 cases blind — 21 disagreement cases and a 50-case
stratified sample of convergent ones — against case evidence only, with no judge
verdicts in the worksheet. The weighted override rate is **0.213** against a
**≤ 0.10** target.

The REAL-GAP stratum was the one the sampling design over-weighted precisely to
scrutinise, and it went **12 of 12**. But it is not what fails the gate.
**EXISTING-RULE-MISBEHAVIOR overrode 7 of 12 and contributes 0.149**, against
REAL-GAP's 0.064, because its population is 1,161 against 289. **Set REAL-GAP
aside entirely and the gate still fails at 0.149.**

The two strata carrying 68% of the population — CORRECT-DETECTION and
GENERATOR-ARTIFACT — had **zero** overrides across 23 cases.

## Corpus-wide agreement

N = **4,556** on every pairwise κ, after last-wins dedup (below).

| | κ |
|---|---:|
| Cohen A–B | 0.6945 |
| Cohen A–C | 0.7595 |
| Cohen B–C | **0.8534** |
| Fleiss (3 raters) | 0.7685 |
| raw agreement ≥ 2-of-3 | 0.9954 |

The raw agreement is the same fact as the triage split: 21 disagreement cases out
of 4,556 is 0.46%.

### Dedup policy, and why N had to be stated

The three judgment files carry **different line counts** — 5,105 / 4,635 / 4,919
against 4,556 cases — because retries and resumes leave duplicate records. Each
file nonetheless contains exactly **4,556 distinct `case_id`s**, and all three
pairwise intersections are 4,556, so coverage is complete and no case is missing
from any judge.

`align_trios` (`src/uofa_cli/adversarial/judge/triage.py:185-190`) builds
`{j.case_id: j for j in judgments}`, a dict comprehension, so the shipped
pipeline is **last-wins**. That dedups rather than double-counting, which is why
every pairwise κ is computed over 4,556 and not over 5,105.

This is stated rather than assumed because a join that silently drops the
shortfall or double-counts a retry would move every figure in this report without
announcing itself.

## Retry characterisation

| Judge | records | distinct | extra | self-conflicting |
|---|---:|---:|---:|---:|
| A | 5,105 | 4,556 | 549 | **38** |
| B | 4,635 | 4,556 | 79 | 8 |
| C | 4,919 | 4,556 | 363 | 1 |

"Self-conflicting" means a case where that judge's own retries disagree with each
other — **47 judge-case pairs** in total. For those, last-wins is a real choice
and not a formality.

**Judge A is an outlier twice over.** It has the most retries, the most
self-conflicts, and the lowest agreement with the author on the hard cases
(1 of 21, below). Its pairwise κ are also the two lowest (0.695 with B, 0.759
with C, against B–C's 0.853). Whatever A is doing, the other two judges agree
with each other considerably more than either agrees with A.

## Spot-check override rate

Fifty convergent cases, stratified by ensemble majority verdict rather than
proportionally, so per-stratum rates are the primary readout and the population
estimate is recovered by reweighting.

| Stratum | n | overridden | rate | weight | contribution |
|---|---:|---:|---:|---:|---:|
| CORRECT-DETECTION | 15 | 0 | 0.000 | 0.5903 | 0.0000 |
| **EXISTING-RULE-MISBEHAVIOR** | 12 | **7** | 0.583 | 0.2560 | **0.1493** |
| GENERATOR-ARTIFACT | 8 | 0 | 0.000 | 0.0878 | 0.0000 |
| **REAL-GAP** | 12 | **12** | **1.000** | 0.0637 | 0.0637 |
| OUT-OF-SCOPE | 3 | 0 | 0.000 | 0.0022 | 0.0000 |
| | **50** | **19** | | **1.0000** | **0.2130** |

**Weighted override rate 0.2130. Target ≤ 0.10. FAIL, as measured.**

Where the overrides went:

- **EXISTING-RULE-MISBEHAVIOR → 4 GENERATOR-ARTIFACT, 3 CORRECT-DETECTION.** The
  ensemble read a rule as misbehaving where the author read either a package that
  never instantiated its defeater, or a rule behaving correctly.
- **REAL-GAP → 12 OUT-OF-SCOPE**, all twelve.

## Author versus judge, on the 21 disagreement cases

| | matches author |
|---|---:|
| Judge A | **1 / 21 (0.048)** |
| Judge B | 8 / 21 (0.381) |
| Judge C | 8 / 21 (0.381) |

The author's verdict matched **some** judge in 17 of 21, so in **4 cases the
author chose a verdict no judge in the trio had offered**. On cases where three
judges could not reach 2-of-3, the author agreed with the ensemble's own spread
about four times in five, and stepped outside it once in five.

## Gap-probe grounding

Run separately by `check_gap_probe_grounding.py` (see its README for the
question). Over 990 gap-probe judgments:

| Slice | n | median distinctive tokens echoed | zero-echo |
|---|---:|---:|---:|
| all gap-probe judgments | 990 | 16 | **0.0%** |
| REAL-GAP, probe points at a Tier-1 candidate | 350 | 15 | **0.0%** |
| REAL-GAP, probe points at **no** candidate | 496 | 17 | **0.0%** |

**Scope sentence, which matters here:** this measures whether a judgment echoes
tokens distinctive to the package, i.e. whether the judge read the package. It
does **not** measure whether the verdict was right. A judgment can be fully
grounded in package content and still reach a verdict the author overturns.

That is exactly what happened. The 12-of-12 REAL-GAP override is **not** judges
confabulating from the prompt header — including the 496 verdicts whose probe
points at no Tier-1 candidate at all, where the header gave them nothing to work
from. It is a genuine disagreement about what counts as a gap.

## Caveats

**Small denominators.** REAL-GAP is 12 cases and OUT-OF-SCOPE is 3. The
adjudication instructions call the latter "indicative only" and warn that 12
cases "can distinguish rare from common but cannot pin a rate to two decimal
places". The 0.213 headline should be read as "roughly double the target", not as
three significant figures.

**The dedup-policy split does not move any figure here.** The pipeline contains
two policies — `align_trios` is last-wins, `check_gap_probe_grounding.py` keeps
first occurrence — and they disagree on the 47 self-conflicting pairs.
Recomputing all 50 convergent majorities under first-wins changes **zero** of
them; only 1 convergent case has a conflicting retry at all, and it does not flip
a 2-of-3 majority. **The override rate is 0.2130 under both policies.** The
inconsistency is real and should be reconciled, but no number in this report
depends on which policy is chosen. Recommendation in *Method notes*.

**The judges judged generation-time behaviour (R1b).** The corpus was generated
2026-04-26 against the catalog of that date. Under the current catalog, **63 of
65 comparable packages have diverged** from their recorded `rules_fired` — traced
to the `(?claim rdf:type uofa:Claim)` guard added in `205cc90e` on 2026-04-27,
one day after the corpus date, which silenced W-EP-01 on 63 packages and cascaded
into COMPOUND-01 (39) and COMPOUND-03 (31). Six further packages are not
comparable at all, having recorded `rules_fired: []` because they failed SHACL
before rules ran. See [INV-21](../../docs/investigations/INV-21-claim-node-conventions.md).

Per R1b the adjudication stands as ruled, against recorded generation-time
`rules_fired`. Two rows are affected in a way worth naming:

| Row | Package | Target | Recorded | Current catalog | Ruled |
|---|---|---|---|---|---|
| **#3** | `adv-2026-p2-021-compound-01_medium_morrison-cou1-v04` | COMPOUND-01 | fired | does not fire | CORRECT-DETECTION |
| **#65** | `adv-2026-p2-010-w-al-02_medium_nagaraja-cou1-v02` | W-AL-02 | did not fire | fires | CORRECT-DETECTION |

Row #65's rule was itself rewritten on 2026-04-27 (`3cd9a5ff`), moving
`hasUncertaintyQuantification` from a per-validation-result attribute to a
top-level boolean. The package carries the defeater the spec asked for — UQ
declared, no `hasSensitivityAnalysis` — and the current rule detects it; the
older rule looked at a level the package does not populate.

**Basis statement (R1b, verbatim).** Stage 4 adjudicated against recorded
generation-time `rules_fired`. The completed worksheet stands as ruled, including
rows #3 and #65. This report carries one disclosure: 63 of 65 comparable packages
have diverged from their recorded `rules_fired` under the current catalog, traced
to the guard added in `205cc90e`.

## Author verdict distribution

Across all 71 rows: CORRECT-DETECTION 23, OUT-OF-SCOPE 21, GENERATOR-ARTIFACT 19,
EXISTING-RULE-MISBEHAVIOR 8. **No row was ruled REAL-GAP or UNCERTAIN**, though
both are available in the verdict vocabulary and the calibration set carries five
of each.

The 21 OUT-OF-SCOPE rulings are all gap probes, under the policy the author
settled during the sitting: a real weakness that is substantive or prose-level
rather than structural is OUT-OF-SCOPE, because no catalog rule can reach it.
The interpretation of that concentration is the author's (R2) and is not taken
here.

## Method notes

Corpus-wide agreement:

```bash
uofa adversarial adjudicate --judgments-a dev/build/adversarial/phase3/production/run-1/judgments_A.jsonl --judgments-b dev/build/adversarial/phase3/production/run-1/judgments_B.jsonl --judgments-c dev/build/adversarial/phase3/production/run-1/judgments_C.jsonl --out dev/build/adversarial/phase3/adjudication/
```

Everything else:

```bash
PYTHONPATH=src python studies/phase3_stage4/rederive_stage4.py
```

The completed worksheet was exported from `Stage 4 adjudication.xlsx` to
`dev/build/adversarial/phase3/triage/adjudication_worksheet.csv`, preserving the
original 35-column schema; the blank original is kept beside it as
`adjudication_worksheet.BLANK-ORIGINAL.csv`.

**Dedup reconciliation, recommended not implemented.** Adopt **last-wins**
pipeline-wide and make it explicit rather than emergent. It is what `align_trios`
already does, so it is what every shipped figure was computed under, and adopting
first-wins would silently restate the triage the whole of Stage 3 and 4 rests on.
A retry is a re-run after a failure, so the last record is the one that completed.
The change is to `check_gap_probe_grounding.py` and to a one-line docstring on
`align_trios` naming the policy. Deferred to the author as an escalation note.

## Coverage statement

Searched: all three judgment files for record counts, distinct case coverage and
self-conflict; `adjudication_sample_key.csv` and `adjudication_queue.csv` for
strata, weights and per-judge verdicts; the completed worksheet for author
verdicts; `agreement_stats.json` for κ. Verified: join completeness both
directions, stratum counts against the declared table, weights summing to 1.0000,
21 + 50 = 71, and the weighted rate recomputed by hand against the script.

Not measured here: whether the ensemble's verdicts are *correct* — only whether
the author agrees with them; the grounding checker's scope sentence above applies
to the same limit. Not re-run: P25-A or any Stage 4 re-adjudication (R1b, R1c).
