# The negative control never produced a package. The test that failed was the contrast case.

Triage of `test_control_produces_no_package.py`, escalated ahead of the
committee meeting on the reading that a negative control was producing a
conforming package. **It is not, and it never was.** The premise came from the
filename, which is a fair reading of `test_control_produces_no_package.py ::
FAILED` and is wrong.

## What passes and what failed

| test | subject | status |
|---|---|---|
| `test_the_constant_cannot_be_imported_at_all` | **the control** | PASS throughout |
| `test_the_empty_control_cannot_be_imported_either` | **the control** | PASS throughout |
| `test_the_constant_covers_one_required_property_of_nine` | the control | PASS |
| `test_the_empty_control_covers_none` | the control | PASS |
| `test_detection_f1_is_still_needed…` | the controls | PASS |
| `test_the_llm_output_does_import_and_is_then_judged_on_content` | **the LLM's real output** | FAILED |

Every assertion about the negative control passes. `control_constant_list`
still fails `uofa import` on the Minimal profile, three sheets before
ProfileComplete is considered, and `validate_extracted` still returns
`conforms is None` for it — the deliberate third value meaning *produced no
package*, distinct from *produced an invalid one*.

**C2's completeness enforcement is not in question from this test.**

## What the failing test was actually pinning

It was the *contrast* case — the one whose job is to show that a real
extraction clears import and is then judged on content, so that the control's
failure means something. It asserted:

```python
assert "placeholder:wasDerivedFrom" in findings
```

That is an assertion that a **defect is still present**. The defect:
`wasDerivedFrom` was satisfied by the workbook template's own help text, `"DOI,
report number, or URI"`, which JSON-LD coerces to a `file://` URI that satisfies
`nodeKind sh:IRI`. A required provenance property met by the instructions for
meeting it, on 59 of 59 workbooks.

The test's own message named the outcome: *"if this cleared, the
source_document prompt fix has taken effect and the shipped-corpus figures in
docs/keyless-extract-findings.md are stale."*

## Verdict: (a) — the fix took effect, confirmed by direct inspection

`_stamp_source_documents` sets `source_document` from the files the pipeline
actually opened, on the reasoning that the pipeline knows their names and a
model guessing at them can only be wrong. Importing the bundle and reading the
package:

    wasDerivedFrom -> "appendix.md; report.md"
    "DOI, report number" present anywhere in the package: False

The property is satisfied by real filenames. The placeholder detector reports
nothing because there is no placeholder.

**Not (b) — the check did not stop reaching what it checked.**
`placeholder_satisfied` is a substring scan for the exact help string, and that
string is genuinely absent from the package. Verified in both directions: the
detector returns `[]` on the real value and `["wasDerivedFrom"]` on planted help
text.

**Not (c) — the control does not produce a conforming package.** See the table.

## What was changed

The assertion is inverted: it now pins that `wasDerivedFrom` is **not**
placeholder-satisfied, with the history in the docstring. A required provenance
property regressing back to being met by its own instructions is worth a test;
a test demanding the defect stay present is not.

A negative assertion passes just as happily when its detector breaks as when
the defect is fixed — the vacuous-pass shape AGENTS.md §13 names. So
`test_the_placeholder_detector_still_fires_when_a_placeholder_is_there` is added
as the positive control, exercising the detector on text that does contain the
help string.

`docs/keyless-extract-findings.md` is corrected: its `wasDerivedFrom` row
describes a defect that has been repaired, and now says so with the date and the
mechanism.

## The naming lesson, which is the transferable part

A file called `test_control_produces_no_package.py` contains six tests, five
about the control and one about the contrast case. When the contrast case fails,
the summary line reads exactly like the control failing — and it was escalated
to pre-committee priority on that reading, by two people independently.

The file name states a *claim*; the tests inside include the claim's *foil*. If
a test file's name is the thing a reader will infer from a failure, the tests
that do not support that claim need names that say so, or they belong in
another file. Left as a note rather than a rename: renaming now would break the
link from the escalation to the record of it.

## Cost of the escalation

Roughly an hour, and the answer is a docs correction plus an inverted assertion.
Worth stating plainly rather than quietly closing: prioritising it ahead of the
committee meeting was the right call **on the information available**, because
"the negative control passes" would have been exactly as serious as it sounded.
Checking which of six tests failed before escalating would have cost two
minutes.
