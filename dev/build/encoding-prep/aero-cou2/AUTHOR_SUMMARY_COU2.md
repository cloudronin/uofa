# Author summary — aero COU2

**Cruise steady-state peak temperature and creep life. Ten-minute read. Your assent to this page
is the review act, so it is complete by construction: every correction and every verdict is here.**

Date prepared: 2026-08-21 · Package `aero-cou2.jsonld`, unsigned · Protocol `Encoding_Protocol_v0_1.md` v0.1

> **This package's decision is `Not accepted`** — the first such record committed anywhere in
> the project, and the case Part B has been waiting on for its Not-Applicable-versus-Overruled
> worked example. Queued in `docs/protocol-v0_2-notes.md`.

---

## 1. What the cell walk corrected

**Two cells changed.** COU2 was the cleaner of the pair by a wide margin.

| Cell | Old → New | Source anchor | Why |
|---|---|---|---|
| `Validation Results` **C3** | `Stable URI or local ID` → *(blank)* | source-absent | Template hint text in a data row, reaching the package as the **node identifier**. Same defect as COU1. See finding below |
| `Credibility Factors` **F17** | rationale + declination sentence | narrative §4.3 | Fail-loud declination for the film-cooling gap the pack cannot express (G-06) |
| **27 anchors**, all sheets | candidate → resolved | per row | **Zero `CANDIDATE` markers remain** anywhere in the workbook. 19 factor rows resolved against the ground truth's `source_file`; 8 rows on `Model & Data` and `Validation Results` have no GT counterpart and were resolved by opening the bundle |

**Levels: 19 of 19 factors matched the pre-registered ground truth exactly** — required, achieved
and status, with required compared strictly. No level divergence anywhere, and no masked
shortfall. Independently corroborated by narrative §6: *"Verification factors (1.1-1.5): all 5
Assessed at or above required level."*

**No merge occurred here.** Unlike COU1, factor 13 is `not-assessed` per §6 open item 5, so
nothing was suppressed and nothing needed un-merging.

Ledger totals: **19 confirmed · 28 corrected · 1 blanked · 48 decisions.** The corrected count is
almost entirely anchors; only two *values* changed, both listed above.

One anchor is worth a look: the `Model & Data` dataset row cites
`cascade_reuse_traceability.txt`, not the dataset itself. The dataset
(`cascade_rig_temperature_data.csv`) lives in **COU1's** bundle, and the in-bundle document that
carries its use here is the re-use record TRC-CRUISE-VAL-001, which names the source dataset and
states the operating-point mismatch. Anchoring to a document outside the evidence boundary would
have been the alternative, and the boundary rule forbids it.

---

## 2. One finding

**protocol-check was blind exactly where the leak lives.** Identical to COU1: the package
carried a `ValidationResult` whose `id` was the literal string `Stable URI or local ID` while
protocol-check reported `✓ no template placeholder text in data rows — clean`. The scan starts at
row 4; the extractor writes its first data row into the template's hint row, row 3. Filed once,
covering both packages, with the fix at both layers — scan from `head + 1`, and refuse any node
whose id matches the hint set.

**COU1's ground-truth defect has no counterpart here** (G-07). COU2's GT expects required 2 /
achieved 2 on Numerical solver error and the workbook agrees. Recorded as a deliberate absence so
the two logs read in parallel.

---

## 3. Dispositions

Full table in `DISPOSITIONS_DRAFT.md`. **16 firings across 8 patterns.**

| Verdict | Count | Basis |
|---|---|---|
| **Confirmed** | 11 | Johnson D-01, D-02, D-10, D-11 and Part B family rules |
| **AUTHOR-RULE** | 5 firings, 1 pattern | judgment class — question below |
| **Not Applicable** | 0 | all five evidence nodes are `ValidationResult` |
| **Compounds** | 0 | see below |

Three worth a glance:

- **No compound patterns fire**, against six on COU1. They key on coexistence with `W-AR-02`,
  which cannot fire here because the decision is Not accepted rather than Accepted-over-a-shortfall.
  The decision outcome changes the firing profile, which is the axis the v0.2 worked example turns on.
- **A2-03** is the sharpest SF-5 instance in either package: the comparator is written as a
  *filename*, `cascade_rig_temperature_data.csv (take-off conditions)`. The source identifies the
  referent precisely and the schema still cannot hold it.
- **A2-05** widens SF-5's shape: its comparator is an **acceptance criterion**
  (`"peak temperature <= 1080K at P95"`), not an artifact. SF-5's proposed referent vocabulary
  would need to cover thresholds as well as entities.

---

## 4. AUTHOR-RULE — 2 questions

**Q1 · `W-EP-04` ×5 [High] — five not-assessed factors at MRL 4.**
Part B: judgment class, calibration **uncalibrated**. The five are Model form, Test conditions,
Equivalency of input parameters, Output comparison, and Relevance of validation activities. The
source presents them not as five gaps but as one, with a single root:

> §4.2: *"The cascade (Re 1.20e6) is outside the cruise operating envelope (Re 0.85e6), not
> within it. The validation is not relevant to the cruise COU."*

> §6: *"Systematic applicability gap (single root cause, 5 Not Assessed factors)"*

**The judgment is unusually well-posed here, because the decision already agrees with the
pattern.** The outcome is Not accepted, qualified *"cruise validation evidence required"* — so
the assessment itself says these gaps undermine the claim. **Decidable question:** does that make
the five firings Confirmed (the pattern correctly reports a real, decision-acknowledged flaw), or
does a decision that already refuses acceptance mean the pattern is reporting something the
package has already accounted for? This is the same shape as COU1's Q1 with the decision
inverted, and ruling both together is what makes the pair a worked example.

**Q2 · Namespace confirmation.** `https://github.com/cloudronin/uofa`, identical to Johnson's
A-27. Covered by the signature and unchangeable after. **Confirm as minted?**

---

## 5. Sign-readiness — stated exactly

| Gate | State |
|---|---|
| `--protocol-check` | **9 of 9 green** |
| C2 SHACL | **pass** |
| C3 Rules | **pass** — 16 firings, all dispositioned above |
| C1 Integrity | **fails, correctly** — zero-filled placeholders. Passes on signing; Johnson F-6d's condition, not a defect |
| Public-wheel round-trip | **NOT PERFORMED.** No wheel is built in this tree and I did not fetch one. Flagged rather than claimed |
| Signing | not performed — yours alone |

**Blocking before signature:** Q1, Q2, and your assent to §1.

