# April ground-truth delta — aero cou2 (cruise)

**AWAITING-AUTHOR. Prepared, not adjudicated.** Per W4 this is a comparison, not a
verdict. Rows are version-labeled per the C5 convention: the expectations were written
in April against an April catalog, and R1a plus the v0.5.x rule refinements landed
after. A difference is a labeled delta, not a failure.

Ground truth: `tests/fixtures/extract/ground_truth/aero-cou2-nasa7009b.json`
Observed: `rules-report.txt`, 15 weakeners across 8 patterns

## Deterministic core fires

| Pattern | April expectation | Observed | Verdict |
|---|---|---|---|
| W-EP-04 | 3 to 5 | 5 | meets |

## Structural invariants

| Invariant | Expected | Observed | Verdict |
|---|---|---|---|
| total_count_min | 5 | 15 | meets |
| total_count_max | 40 | 15 | meets |
| w_ep_04_count_min | 3 | 5 | meets |
| w_ar_02_count_exact | 0 | 0 | meets |
| w_ar_02_count_exact_rationale | _(rationale, not a check)_ | | |

## Must not fire

| Pattern | Observed | Verdict |
|---|---|---|
| W-AR-02 | 0 | meets, hard gate held |

## Import-dependent fires

April marks these as varying with how the import binds evidence, so they carry no
pass or fail. They are listed because the pattern of what did and did not fire is
the useful part.

| Pattern | April note | Observed |
|---|---|---|
| W-AR-01 | mass_fire_risk: see COU1 ground truth notes. Factors with requiredLevel but no acceptanceCriteria; 14-19 fires possible if prompt not tuned. | 0 |
| W-NASA-02 | possible | 1 |
| W-NASA-03 | possible | 1 |
| W-NASA-05 | possible: fires if cruise_uq_study.csv does not link as uofa:hasUncertaintyQuantification on factor 17 | 0 |
| W-NASA-06 | possible: fires if sensitivity_study_cruise.csv does not link as SensitivityAnalysis evidence on factor 18 | 1 |
| W-AL-01 | possible | 0 |
| W-AR-05 | possible | 4 |
| W-EP-01 | possible | 0 |
| W-EP-02 | possible | 0 |

## The one delta worth the author's attention

**W-AR-01 fired zero times against an April baseline of 14.** The ground truth records
it as a mass-fire risk that "fires for every factor with requiredLevel but no
acceptanceCriteria", with 14 fires of baseline noise on the then-current aero package,
and names the prompt fix that was meant to address it. The fix has landed: the extractor
now returns acceptance criteria on every factor, so the pattern has nothing to fire on.

That is a labeled improvement rather than a failure, and it is the clearest thing in
this table that changed between April and now. Whether the criteria it returns are
*correct* is a question for the cell walk, not for this comparison.
