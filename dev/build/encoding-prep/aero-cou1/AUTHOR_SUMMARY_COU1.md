# Author summary — aero COU1

**Take-off transient peak metal temperature. Ten-minute read. Your assent to this page is the
review act, so it is complete by construction: every correction and every verdict is here.**

Date prepared: 2026-08-21 · Package `aero-cou1.jsonld`, **SIGNED 2026-08-21** · Protocol `Encoding_Protocol_v0_1.md` v0.1

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
| **Confirmed**, mechanical | 11 | Johnson D-01, D-02, D-06, D-10, D-11 and Part B family rules |
| **Confirmed**, judgment class | 3 | author rulings 2026-08-21 — §4 |
| **Confirmed**, cascading compounds | 7 | Part B: compounds inherit their bases. Bases now Confirmed, so the cascade resolves |
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

## 4. Rulings — all issued 2026-08-21

**No open questions remain.** The draft raised three; the author ruled all three, together with
COU2's, as one set.

| # | Question | Ruling |
|---|---|---|
| Q1 | `W-AR-02` ×2 [Critical] — does the reasoning hold? | **Confirmed**, and **the decision stands as carried.** |
| Q2 | `W-EP-04` [High] — unassessed factor at MRL 3 | **Confirmed**, judgment class |
| Q3 | Namespace | **Keep as minted** |

**Q1 — Confirmed, and `Accepted (with conditions)` stands.** Confirmed on Part B's own
`W-AR-02` clause: *"an acceptance standing above a recorded shortfall"* — the decision is Accepted
while Discretization error (3/1) and Relevance of validation activities (3/2) carry achieved below
required. The decision stands because the source's board accepted at MRL 3 for a concept-stage
screening use with the gaps named and conditions attached (probabilistic UQ, ground test before
the next rung), and the package carries those gaps loudly. **An accepted decision *over* displayed
weaknesses is what the framework is for.** The weakeners are Confirmed, the decision is the
source's, and the two coexist on the record.

> **One correction to the ruling's stated rationale.** The ruling described the basis as *"the
> declared method and the activity type disagree as carried."* That is **`W-AR-03`'s** rule
> (Part B, argumentation-method, mechanical), not `W-AR-02`'s — and `W-AR-03` does not fire on
> this package. The verdict is unaffected: `W-AR-02`'s own clause covers this firing squarely on
> the acceptance-above-shortfall limb, which is how it is recorded. Flagged rather than
> transcribed, on the same basis as Johnson E-1.

**Q2 — Confirmed**, under the shared `W-EP-04` rule applied identically to COU2. Results
uncertainty is `not-assessed` at MRL 3 and §5.4 states probabilistic UQ is required there, so as a
package fact the unassessed factor at elevated risk does undermine the claim. The disposition
notes that **the decision already prices it**: the conditions attached to the acceptance exist
because of these gaps.

**Q3 — Keep as minted.** `https://github.com/cloudronin/uofa`, same resolution as Johnson A-27.
Third package minting identically.

### The pair

COU1 and COU2 were ruled together and demonstrate the tier logic's one essential job:
**identical weaknesses, different contexts of use, opposite defensible decisions.** Take-off
concept screening accepts with conditions; cruise creep-life declines. Queued as v0.2's second
worked example.

---

## 5. Sign-off — complete

| Gate | State |
|---|---|
| `--protocol-check` | **9 of 9 green** |
| C2 SHACL | **pass** |
| C3 Rules | **pass** — 21 firings, **all Confirmed and all adjudicated** |
| Dispositions | **complete** — no AUTHOR-RULE rows remain |
| C1 Integrity | **pass** — signed 2026-08-21 |
| Public-wheel round-trip | **pass** — published `uofa==0.12.0`, clean venv, package outside the repo. C1 ✓ C2 ✓ C3 ✓, cross-version against the 0.11.0 import |
| Signing | **done**, by the author with the research key |

**Nothing remains.** Assent given, signed, verified locally and against the published wheel.
