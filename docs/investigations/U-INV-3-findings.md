# U-INV-3 — D6 number traceability

Status: **ESCALATED — unchanged in substance, more urgent under parent spec v2.0**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent D6, A6; shares its pin check with INV-6

---

# ADDENDUM — re-investigated against parent spec v2.0

## v2.0 promotes the contested sentence to load-bearing manuscript text

v1.1's D6 said only *"U-INV-3: every number traces to committed artifacts."* v2.0
§D6 clause 3 writes the sentence:

> New §4.x (one to two pages): cohort table; **W-AL-01 firing 384/427 and clearing
> exactly the results carrying real uncertainty**, framed as the invariance
> demonstration (the same unmodified rule assesses blood-pump CFD and LLM benchmark
> evidence and discriminates). One sentence of finding, no field-reform rhetoric;
> **Demonstrated rung (D7)**.

Both contested elements are now specified manuscript text, and D7 places them on
the **Demonstrated** rung — defined in v2.0 as *"machine-re-derivable evidence…
reproducible by reader."* That raises the bar on both findings rather than lowering
it:

| Finding | Was | Is now |
|---|---|---|
| **384 is prose arithmetic, not a measured firing count** (§1) | a traceability gap | a **Demonstrated-rung claim that is not machine-re-derivable**. No committed script runs the rule engine over the cohort; `measure_cohort.py` measures furnishing rates only. A reader following D7's own definition cannot reproduce 384. |
| **The equality claim's second direction is unverified** (§3) | a two-sided check that failed one side | a **biconditional printed in Ch4** and tagged Demonstrated, whose converse rests on `_find_stderr` matching only key paths containing the substring `stderr` ([raidex.py:129-157](src/uofa_cli/furnishers/raidex.py)) |

## The invariance framing is the part worth protecting, and it survives either fix

v2.0's framing — *the same unmodified rule assesses blood-pump CFD and LLM benchmark
evidence and discriminates* — is a strong claim and it is **fully supported** by
what is committed. It needs only:

- W-AL-01's rule body, unchanged since the v0.5.15.1 freeze (INV-6 §2 establishes
  byte-identity), and
- the furnishing split 43/427, which is committed in
  [`results.json`](studies/cohort-2026-08/results.json) and re-derivable via
  `measure_cohort.py`.

Neither depends on the 384 count or on the biconditional. **Recommendation
unchanged and now easier to act on: take §1 option 1 and §3 option 1** — report the
furnishing split as the measured figure and state W-AL-01's behaviour as its
consequence, which is how `studies/cohort-2026-08/README.md:52` already phrases it
internally. The invariance sentence keeps all its force and the Demonstrated tag
becomes true.

If the author prefers the stronger wording, both measurement options remain costed
(~2h to make 384 a measured firing count; ~1h for the completeness scan that would
earn the biconditional). Doing both, at ~3h, is the only route by which v2.0's D6
clause 3 can be written exactly as drafted **and** carry the Demonstrated tag
honestly.

## One additional v2.0 dependency

§D6 clause 2 requires the new §3.4.x to state *"what runs (completeness factors +
core ValidationResult rules, all machine-re-derivable)"*. That phrase commits to
machine-re-derivability for the whole external arm, not just W-AL-01. The
re-derivation script exists for the **furnishing** measurement
(`measure_cohort.py`, revision-pinned) but **not for the rule-firing side**. The
same ~2h that lands 384 as a measurement also makes clause 2's parenthetical true.

## Coverage statement (addendum)

**Searched.** v2.0 §D6 clauses 1-4, §A6, §D7's rung definitions and contents.
Re-checked against the artifacts established in the original finding; no new code
or data reading was required, because v2.0 changes the *status* of these numbers
(prose plan → specified manuscript text on a named claims rung), not their
provenance.

**NOT verified — unchanged.** The 427 `raw` blocks live in the HF dataset
`cloudronin/raidex-results` at revision `d459f536…`, not in this repo, so the
equality claim's second direction still cannot be settled from the repository.
`measure_cohort.py` was not executed.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Trace table

| # | Number | Committed artifact | Commit | Re-derivable? | Verdict |
|---|---|---|---|---|---|
| 1 | **32,111 cards** | [studies/taxonomy-validation/frame.json:11](studies/taxonomy-validation/frame.json) `"n_cards": 32111`; corroborated at [enrichment/liang/manifest.json:16](studies/taxonomy-validation/enrichment/liang/manifest.json) `"rows_scanned": 32111` | `cbb1b6e1` / `d3d07bd2` (2026-08-10) | Yes — `studies/taxonomy-validation/frame.py --corpus <modelcard_info.parquet>` | **TRACED** |
| 2 | **Pin `6bcc76fe6142`** | [studies/taxonomy-validation/PREREGISTRATION.md:100-101](studies/taxonomy-validation/PREREGISTRATION.md), with a content pin (`sha256:79aa662d94d0112f13043f420d996347…`, 31,620,407 bytes) | `d3d07bd2` (2026-08-10 22:12) | n/a (a pin) | **TRACED — single occurrence, see §2** |
| 3 | **raidex model/result counts (43 models, 427 validation results)** | [studies/cohort-2026-08/results.json](studies/cohort-2026-08/results.json) `"n_models": 43`, `"n_validation_results": 427`; dataset revision `d459f536b506dc5f82355891db19f599f374a92c` pinned in the script | — | Yes — `python studies/cohort-2026-08/measure_cohort.py` | **TRACED** |
| 4 | **W-AL-01 firing 384/427** | **No artifact records 384.** It appears only as prose at [studies/cohort-2026-08/README.md:52](studies/cohort-2026-08/README.md) and [docs/model-credibility-pack-spec.md:422](docs/model-credibility-pack-spec.md) | — | Arithmetic only: 427 − 43 | **BLOCKER — see §1** |
| 5 | **"clears exactly the N carrying real uncertainty" (N = 43)** | `results.json` `furnished_counts.hasUncertaintyQuantification = 43` | — | Direction 1 yes; **direction 2 no** | **ESCALATED — see §3** |

## 1. Blocker: 384 is inferred, never measured

`studies/cohort-2026-08/measure_cohort.py` measures **furnishing rates** — which
Group-B properties the raidex records carry. Grepped for `rules`, `jena`,
`W-AL-01`: the script maps properties to the rules they feed
([measure_cohort.py:52](studies/cohort-2026-08/measure_cohort.py)
`"hasUncertaintyQuantification": "W-AL-01 (core)"`) but **never runs the rule
engine**. No artifact in `studies/` contains a W-AL-01 firing count.

384 is therefore a correct arithmetic consequence of a committed measurement
(427 − 43), stated in prose, not a measured result. That distinction matters
precisely because D6's sentence presents it as a detection outcome.

Two ways to close it, author's choice:

1. **Cheapest, honest:** reword D6 so the reported figure is the furnishing rate
   (43/427 · 10.1%) and W-AL-01's behaviour is stated as its consequence — which is
   how `README.md:52` already phrases it internally. No new run.
2. **Strongest:** add a step to `measure_cohort.py` that builds the 427-result
   bundle and calls `uofa_cli.commands.rules.run_structured` over it, writing an
   observed firing count into `results.json`. Then 384 is measured, and D6's
   sentence needs no hedge. Estimate ~2h; the invocation pattern already exists at
   [adversarial/classifier.py:206-226](src/uofa_cli/adversarial/classifier.py).

Per the item's own rule — *"D6 drafting must not begin for that number until it
lands in `studies/`"* — option 1 is a reword that removes the number from the
blocker list; option 2 lands it.

## 2. Pin consistency (shared with INV-6 step 4)

`6bcc76fe6142` occurs in **exactly one** file repo-wide:
`studies/taxonomy-validation/PREREGISTRATION.md:101`. Verified by
`grep -rn "6bcc76fe6142"` across the whole tree. It is trivially self-consistent,
and nothing else cites a differently-abbreviated Liang commit (the only other
12-hex strings under `studies/` are `eeab18c150b2`, `574916ea6346`,
`063dc98c441d`, none of which is a Liang pin).

**But the frame it pins is cited elsewhere with the wrong source file**, which is
the same defect class the pre-registration exists to prevent:

| Location | Says | Correct value |
|---|---|---|
| [docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md:32](docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md) | "Liang `datasetcard_info.parquet` (32,111 cards…" | `modelcard_info.parquet` |
| [studies/taxonomy-validation/frame.py:4](studies/taxonomy-validation/frame.py) (usage docstring) | `--corpus <datasetcard_info.parquet>` | `modelcard_info.parquet` |

The pre-registration corrected this explicitly at
[PREREGISTRATION.md:104-108](studies/taxonomy-validation/PREREGISTRATION.md):
*"A16.2 named the wrong file… Dataset cards and model cards are different objects,
and this pack assesses model cards."* Ten other artifacts carry the corrected name
(`frame.json`, `gold/manifest.json`, `gold/README.md`, `gold/make_gold_set.py`,
`enrichment/search.py`, `enrichment/liang/manifest.json`). Two stragglers were
missed — one of them the script that computes the frame.

**Both are two-word fixes and neither changes a number.** But if the addendum is
cited in D6 or Ch4, it hands a reviewer a source-file mismatch against the
pre-registration. Fix before D6 drafting. (Recorded again in INV-6.)

## 3. The equality claim: two-sided check

D6's sentence: W-AL-01 *"clears exactly the results carrying real uncertainty."*
Checked in both directions, as the item requires.

### Direction 1 — every cleared result carries stated uncertainty: **HOLDS**

- W-AL-01 clears a validation result iff the result carries
  `uofa:hasUncertaintyQuantification` ([rules:107-119](packs/core/rules/uofa_weakener.rules),
  a single `noValue` predicate — nothing else can suppress it).
- The raidex furnisher sets that property **only** from a genuine numeric standard
  error: `stderr = _find_stderr(entry.get("raw")); if stderr is not None:`
  ([furnishers/raidex.py:281-284](src/uofa_cli/furnishers/raidex.py)). The comment
  above it states the intent: *"populated ONLY from a genuine numeric stderr."*
- Cleared ⊆ carries-a-numeric-stderr. ✓

### Direction 2 — every result carrying stated uncertainty is cleared: **NOT VERIFIED, and structurally doubtful**

The set of cleared results is not "results carrying real uncertainty"; it is
"results whose uncertainty `_find_stderr` recognised." Those coincide only if
`_find_stderr` is complete over the corpus's uncertainty vocabulary. Reading it
([raidex.py:129-157](src/uofa_cli/furnishers/raidex.py)):

```python
elif "stderr" in path.lower():
    num = _as_number(node)
```

It walks the `raw` block and matches **only key paths containing the substring
`stderr`**, then requires a numeric value. A result reporting uncertainty as a
confidence interval, a variance, a standard deviation, a bootstrap range, or
quantiles carries real uncertainty and **would not be cleared**. The docstring is
candid that this was tuned to one observed shape: *"Across the published cohort
only `bbq` carries one — its `raw.bbq_generate["acc_stderr,none"]` is a float while
its 26 sub-scores carry the string 'N/A'."*

No committed artifact establishes that no other constituent reports uncertainty in
another form. Confirming direction 2 requires a scan of all 427 `raw` blocks for
uncertainty-shaped keys **outside** the `stderr` substring — which is exactly the
keyword-for-claim substitution the item warns against, currently unperformed.

**Escalation.** D6's central sentence asserts a biconditional; the record supports
one implication. Options:

1. **Weaken to the supported claim** (recommended, zero new work): *"W-AL-01 clears
   the 43 results that publish a numeric standard error and fires on the remaining
   384"* — true, checkable, and it still makes D6's point that the assessment
   discriminates rather than failing everything uniformly.
2. **Earn the biconditional**: add a completeness scan over the 427 `raw` blocks for
   `ci|conf|interval|std|sd|variance|quantile|error` keys, and record the result in
   `results.json`. ~1h. If it returns zero, the equality claim is measured and D6
   can keep its sentence.

## Blocker list (per the item's rule)

| Number | Blocked because | Unblocks by |
|---|---|---|
| **W-AL-01 firing 384** | not recorded in any committed artifact; arithmetic in prose | §1 option 1 (reword) or option 2 (~2h measure) |
| **"clears exactly the N carrying real uncertainty"** | second direction unverified | §3 option 1 (reword) or option 2 (~1h scan) |

Numbers 1, 2 and 3 are clear to draft against today.

## Coverage statement

**Searched.** Repo-wide greps for `32,111` / `32111`, `6bcc76fe6142`, `384`,
`427`, `21,181` / `10,930`, `datasetcard_info` / `modelcard_info`, and
`\b[0-9a-f]{12}\b` across `studies/`. Read `studies/cohort-2026-08/README.md`
(lines 1-80) and `results.json` (lines 1-90);
`studies/taxonomy-validation/PREREGISTRATION.md:95-130`;
`studies/taxonomy-validation/frame.json`. Read
`src/uofa_cli/furnishers/raidex.py:129-157` and `:270-296` in full for the
both-directions check. Grepped `measure_cohort.py` for `rules|jena|W-AL-01|stderr`
to establish that the rule engine is not invoked. Read W-AL-01's rule body
end to end.

**Search terms derived from each claim's own definition:** for the equality claim,
`hasUncertaintyQuantification`, `stderr`, `acc_stderr`, `uqMethod`, `noValue` —
i.e. the furnisher's condition and the rule's condition, checked against each other,
rather than searching for the number 43.

**NOT searched / not verified.**
- **The 427 `raw` blocks themselves were not scanned.** They live in the HF dataset
  `cloudronin/raidex-results` at revision `d459f536…`, not in this repo. Direction 2
  cannot be settled from the repo alone; that is why it is escalated rather than
  reported as failing.
- `measure_cohort.py` was **not executed**, so numbers 1 and 3 are traced to
  committed artifacts and to a documented re-derivation command, but not
  re-derived here. Running it requires network access to the pinned HF revision.
- "The raidex model/result counts D6 will cite" was interpreted as the headline
  43 / 427. If D6 cites per-model or per-constituent counts, those rows exist in
  `results.json` `per_model[]` but were not individually traced.
- The manuscript's D6 sections do not exist yet (Ch4 §4.x is a skeleton — see
  INV-8), so no manuscript occurrence of these numbers could be checked. This trace
  is against the plan in the parent spec, not against drafted prose.
