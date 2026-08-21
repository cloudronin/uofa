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
| **Confirmed**, mechanical | 11 | Johnson D-01, D-02, D-10, D-11 and Part B family rules |
| **Confirmed**, judgment class | 5 | author ruling 2026-08-21 — §4 |
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

## 4. Rulings — all issued 2026-08-21

**No open questions remain.**

| # | Question | Ruling |
|---|---|---|
| Q1 | `W-EP-04` ×5 [High] — five not-assessed factors at MRL 4 | **Confirmed, emphatically**, and **`Not accepted` stands as carried** |
| Q2 | Namespace | **Keep as minted** |

**Q1 — Confirmed**, under the *same* `W-EP-04` rule applied to COU1's Q2, which is what makes it
a rule rather than two decisions. At cruise-creep stakes, five risk-conditioned unassessed factors
are precisely why the source's own answer is Not Accepted: **the firings and the decision agree.**

**The decision stands, and the symmetry is the point.** Same evidence family as COU1. Higher-stakes
context of use. The source declines because the shortfalls that were tolerable for take-off
screening are disqualifying for cruise creep-life, while COU1's board accepted the same evidence
family with conditions attached.

**Q2 — Keep as minted.** `https://github.com/cloudronin/uofa`, same resolution as Johnson A-27.
Fourth package minting identically.

### The pair

**Identical weaknesses, different contexts of use, opposite defensible decisions.** That is the
tier logic doing its one essential job, and it is why the v0.2 worked example is this *pair*
rather than COU2 alone.

---

## 5. Sign-readiness

| Gate | State |
|---|---|
| `--protocol-check` | **9 of 9 green** |
| C2 SHACL | **pass** |
| C3 Rules | **pass** — 16 firings, **all Confirmed and all adjudicated** |
| Dispositions | **complete** — no AUTHOR-RULE rows remain |
| C1 Integrity | **fails, correctly** — zero-filled placeholders. Passes on signing; Johnson F-6d's condition |
| Public-wheel round-trip | **deferred to sign-off**, where it belongs with the signature |
| Signing | not performed — yours alone |

**Remaining before signature:** your assent to §1, then the sign-off step — wheel round-trip,
sign, push.
