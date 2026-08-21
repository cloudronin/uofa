# April ground-truth delta — aero cou1 (take-off transient peak temperature)

**ACKNOWLEDGED 2026-08-21** (see the acknowledgement pass at the end). Prepared here, not adjudicated at the time of writing. Per W4 this is a comparison, not a
verdict. Rows are version-labeled per the C5 convention: the expectations were written
in April against an April catalog, and R1a plus the v0.5.x rule refinements landed
after. A difference is a labeled delta, not a failure.

Ground truth: `tests/fixtures/extract/ground_truth/aero-cou1-nasa7009b.json`
Observed: `rules-report.txt`, 20 weakeners across 11 patterns

## Deterministic core fires

| Pattern | April expectation | Observed | Verdict |
|---|---|---|---|
| W-AR-02 | 2 to 6 | 2 | meets |
| W-EP-04 | 1 | 1 | meets |
| COMPOUND-01 | 1 to unbounded | 6 | meets |
| COMPOUND-03 | 1 to unbounded | 1 | meets |

## Structural invariants

| Invariant | Expected | Observed | Verdict |
|---|---|---|---|
| total_count_min | 5 | 20 | meets |
| total_count_max | 60 | 20 | meets |
| w_ep_04_count_exact | 1 | 1 | meets |
| w_ar_02_count_min | 2 | 2 | meets |
| compound_01_count_min | 1 | 6 | meets |

## Must not fire

Nothing prohibited for this COU.

## Import-dependent fires

April marks these as varying with how the import binds evidence, so they carry no
pass or fail. They are listed because the pattern of what did and did not fire is
the useful part.

| Pattern | April note | Observed |
|---|---|---|
| W-AR-01 | mass_fire_risk: fires for every factor with requiredLevel but no acceptanceCriteria. Baseline noise on current NASA aero jsonld was 14 fires. Step 9 o | 0 |
| W-NASA-02 | possible: fires if review_board_minutes_2026Q1.txt does not link as ReviewActivity evidence on factor 15 | 1 |
| W-NASA-03 | possible: fires if configuration management evidence does not link to factor 16 | 1 |
| W-NASA-06 | possible: fires if sensitivity_study_turbulence_intensity.csv does not link as SensitivityAnalysis evidence on factor 18 | 1 |
| W-AL-01 | possible: fires per validation result without hasUncertaintyQuantification | 0 |
| W-AR-05 | possible: fires per validation result without comparedAgainst | 4 |
| W-EP-01 | possible: fires if claim has no prov:wasDerivedFrom | 0 |
| W-EP-02 | possible: fires per validation result without prov:wasGeneratedBy | 0 |

## The one delta worth the author's attention

**W-AR-01 fired zero times against an April baseline of 14.** The ground truth records
it as a mass-fire risk that "fires for every factor with requiredLevel but no
acceptanceCriteria", with 14 fires of baseline noise on the then-current aero package,
and names the prompt fix that was meant to address it. The fix has landed: the extractor
now returns acceptance criteria on every factor, so the pattern has nothing to fire on.

That is a labeled improvement rather than a failure, and it is the clearest thing in
this table that changed between April and now. Whether the criteria it returns are
*correct* is a question for the cell walk, not for this comparison.

---

## Acknowledgement pass — 2026-08-21

**Acknowledged as prepared. No expectation comparison changed.**

The cell walk's corrections were folded back through the delta table and none of them moves a
deterministic core fire or a structural invariant:

- **`Validation Results` C3 blanked** (template placeholder). This *raised* the `W-AR-05` count
  by one, because clearing the placeholder gave the MMS node a well-formed identifier the rule
  can now reach. The firing was always true of the package; the placeholder was hiding it. No
  April expectation is keyed on the `W-AR-05` count.
- **Factor 13 achieved corrected 1 → 2** (un-merge). `W-AR-02`'s `must_fire_factors` are
  Discretization error and Relevance of the validation activities to the COU. Both still carry
  achieved below required after the correction, so both still fire and `count_min: 2` is met.
- **G-07, the GT defect on Numerical solver error.** The workbook stands at required 1 /
  achieved 1, so this factor never contributed a `W-AR-02` fire and the count is unaffected
  either way. The GT's own rationale had listed it only as a possible additional fire, not a
  must-fire.

**No deterministic-fire miss and no structural-invariant miss.** Nothing here is AUTHOR-RULE.
