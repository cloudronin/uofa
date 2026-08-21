# Author summary — aero COU1

**Take-off transient peak metal temperature. Ten-minute read. Your assent to this page is the
review act, so it is complete by construction: every correction and every verdict is here.**

Date prepared: 2026-08-21 · Package `aero-cou1.jsonld`, unsigned · Protocol `Encoding_Protocol_v0_1.md` v0.1

---

## 1. What the cell walk corrected

Four cells changed. Everything else was confirmed against the pre-registered ground truth
(`tests/fixtures/extract/ground_truth/aero-cou1-nasa7009b.json`) or against the source.

| Cell | Old → New | Source anchor | Why |
|---|---|---|---|
| `Validation Results` **C3** | `Stable URI or local ID` → *(blank)* | source-absent | Template hint text left in a data row. It had reached the package as the **node's identifier**. See finding 1 below |
| `Credibility Factors` **D17** | achieved `1` → `2` | narrative §4.2; §6 open item 4 | The extractor merged narrative §4.3 Film Cooling into factor 13 and took its harsher L1, which suppressed §4.2's own gap. Source rates *this* factor Level 2 |
| `Credibility Factors` **F17** | rationale + declination sentence | narrative §4.3 | Fail-loud. The evicted film-cooling gap is named in the cell and pointed at G-06 |
| **27 anchors**, all sheets | candidate → resolved | per row | **Zero `CANDIDATE` markers remain** anywhere in the workbook. 19 factor rows resolved against the ground truth's `source_file`; 8 rows on `Model & Data` and `Validation Results` have no GT counterpart and were resolved by opening the bundle. Dual where the data file and the narrative each carry half |

**Levels: 18 of 19 factors confirmed as extracted.** Required was compared **strictly** against
the ground truth; tolerance is extraction latitude on *achieved* only.

Ledger totals: **18 confirmed · 29 corrected · 1 blanked · 48 decisions.** The corrected count is
dominated by anchors — only three *values* changed, and they are the first three rows above.

---

## 2. Two findings that are not corrections

**Finding 1 — protocol-check was blind exactly where the leak lives.** Both aero packages
carried a `ValidationResult` whose `id` was the literal string `Stable URI or local ID`, and
protocol-check reported `✓ no template placeholder text in data rows — clean`. Not "skipped" —
an affirmative pass. The string *is* in its hint set; the row *is* populated. The scan starts at
`head + data_offset` (row 4) and the extractor writes its first data row into the template's
hint row (row 3), so the one row where hint text most plausibly survives is the one row never
examined. This is the check written because of Johnson's F-3d, failing on F-3d's own case.
Filed with the fix at both layers: scan from `head + 1`, **and** refuse any node whose id
matches the hint set, because a future writer bug could mint one past a correct workbook scan.
Detection came from reading a node name skeptically, not from any check.

**Finding 2 — the ground truth invented a required level (G-07).** Already ruled by you: the
source wins, the workbook stands at required 1 / achieved 1, the GT row is recorded GT-DEFECT.
No downstream re-measurement.

---

## 3. Dispositions

Full table in `DISPOSITIONS_DRAFT.md`. **21 firings across 9 patterns.**

| Verdict | Count | Basis |
|---|---|---|
| **Confirmed** | 11 | Johnson D-01, D-02, D-06, D-10, D-11 and Part B family rules |
| **AUTHOR-RULE** | 3 firings, 2 patterns | judgment class, no precedent — questions below |
| **Cascading compounds** | 7 | Part B: compounds inherit their bases, not dispositioned individually |
| **Not Applicable** | 0 | all five evidence nodes are `ValidationResult`, so SF-4's node-class exception applies to nothing here |

Two dispositions worth a glance rather than a signature:

- **A1-05**, the Monte Carlo UQ node, is Confirmed in **D-06 stated-absence form, not SF-5**.
  Its `comparedAgainst` is `"N/A"`, and §5.4 confirms the run is uncertainty *propagation* with
  the engine-COU analysis "not executed" — so the package correctly carries no comparator. The
  other four `W-AR-05` firings are SF-5 (real comparators lost at expansion).
- **W-CON-01 never fires.** Your prediction held: no scale boundary exists in a bundle authored
  against its own pack, so the D-07..09 precedent has nothing to transfer to. That escalation
  path is retired.

---

## 4. AUTHOR-RULE — 2 questions

**Q1 · `W-AR-02` ×2 [Critical] — does the reasoning hold?**
Part B makes this judgment class: *"no test of package content settles either."* It fires
because the decision is **Accepted** while factors carry achieved below required. Both shortfalls
are the source's own disclosed conditions, not encoding artifacts:

> §1.3 Discretization Error: *"the blade tip region has NOT been assessed for mesh convergence.
> The tip region … is where peak metal temperature actually occurs during take-off transient."*
> **Achieved Level 1 against Required Level 3.**

> §4.2 Relevance of Validation: *"NOT acceptable extrapolation for cruise, off-design, or
> tip-focused predictions."* **Achieved Level 2 against Required Level 3.**

The decision itself is qualified — *"Accepted (with conditions)"*, with both gaps carried as MRL 4
conditions. **Decidable question:** does an Accepted-with-conditions decision over two disclosed,
condition-carrying shortfalls constitute the flaw `W-AR-02` describes — Confirmed — or does the
qualifier mean the pattern misreads a decision that already accounts for them — Overruled?

**Q2 · `W-EP-04` ×1 [High] — unassessed factor at elevated model risk.**
Part B: judgment class, calibration **uncalibrated**. Results uncertainty is `not-assessed` at
MRL 3, and the source says that is precisely where it is owed:

> §5.4: *"Results uncertainty quantification has NOT been performed for the engine COU peak
> temperature prediction … Per NASA-STD-7009B Factor 5.4, probabilistic UQ is required at MRL 3."*

**Decidable question:** does a not-assessed Results uncertainty at MRL 3 undermine this COU's
claim — Confirmed — given the COU is scoped as *"preliminary blade design screening"*?

**Q3 · Namespace confirmation.** `https://github.com/cloudronin/uofa`, identical to Johnson's
A-27 which you resolved confirmed-by-author. Covered by the signature and unchangeable after.
**Confirm as minted?**

---

## 5. Sign-readiness — stated exactly

| Gate | State |
|---|---|
| `--protocol-check` | **9 of 9 green**, including the ambiguity log, run log and pins |
| C2 SHACL | **pass** |
| C3 Rules | **pass** — 21 firings, all dispositioned above |
| C1 Integrity | **fails, correctly** — signature and hash are the importer's zero-filled placeholders. Passes on signing; this is Johnson F-6d's condition, not a defect |
| Public-wheel round-trip | **NOT PERFORMED.** No wheel is built in this tree and I did not fetch one. Flagged rather than claimed |
| Signing | not performed — yours alone |

**Blocking before signature:** Q1, Q2, Q3, and your assent to §1.

