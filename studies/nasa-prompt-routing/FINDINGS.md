# Every NASA extraction was run on the V&V 40 prompt

Triage of the nasa-7009b COU2 regression (factor F1 **0.593**, gate FAIL),
2026-08-14. The plan asked for this to be classified as a metric artifact, a
segmenter artifact, or a real regression. It is **none of the three**: it is a
shipped wiring bug in `uofa extract`, upstream of both the metric and the model.

## The bug

`paths.extract_prompt()` had no `pack_name` parameter:

```python
def extract_prompt(root: Path = None) -> Path:
    manifest = pack_manifest(root=root)          # no pack
    return pack_dir(root=root) / manifest["prompt"]   # no pack
```

`pack_dir()` with no pack falls back to `active=["vv40"]`, so **every call
returned `packs/vv40/prompts/vv40_extract_prompt.txt`, for every pack**.
`extract_cmd.py:193` called it with no pack and handed the result to
`build_prompt`.

So `uofa extract --pack nasa-7009b` asked the model to fill in the 13 ASME V&V
40 factors. The model did exactly that. The six NASA-STD-7009B factors were
never mentioned to it.

**Nothing downstream noticed**, because everything else was wired correctly:
`_json_to_result` selects `NASA_ALL_FACTOR_NAMES` from the `pack_name` it *was*
given, and the workbook writer pre-fills all 19 rows from the pack. The output
looked like a NASA extraction in which the model had declined to fill six
factors — not like a question that was never asked.

The second symptom was visible in the report the whole time and read as an
ordinary extraction error: `standards_reference: expected 'NASA-STD-7009B', got
'ASME-VV40-2018'`. The model was reporting the standard it had been handed.

## How it was found, and what it was not

The saved raw response was complete and well-formed — 6.4 KB, roughly a tenth of
the 16,384-token output cap, ending in a full `=== DECISION ===` block. Not
truncation.

Every NASA extraction on disk showed the same cut: **13 of 19 factors in 27 of
27** (15 dev bundles, 10 held-out test bundles, both aerospace regression COUs),
with zero variance and no factor emitted outside the thirteen. The per-factor F1
added for the H2 re-run made it unmissable and perfectly bimodal:

| | dev F1 | test F1 |
|---|---|---|
| all 13 V&V 40 factors | 1.000 | 1.000 |
| all 6 NASA-only factors | 0.000 | 0.000 |

The evidence for the six is not subtle. `credibility_assessment_narrative.docx`
carries sections §5.1–§5.6, one per missing factor, each stating its own status
and level in plain text — "Status: Assessed. Level 3." It is the easiest
extraction in the document.

The working hypothesis was prompt-instruction placement: "Include ALL 19
factors" sits ~120 lines below the factor list, and this same model had already
been caught skimming a rule 14 lines below the spec it governed (see
`studies/prompt-absence/`). `probe_nasa_block.py` tested it — arm A the shipped
NASA prompt, arm B the same prompt with the count instruction moved adjacent to
the list, three runs each.

**Both arms returned 19 of 19 factors, 6 of 6, three for three.** The hypothesis
was wrong, and being wrong is what located the bug: the shipped NASA prompt
worked perfectly whenever it was actually delivered, which meant the prompt was
not reaching the model. `paths.extract_prompt()` confirmed it in one line.

The segmenter is not on this path at all — this is LLM extraction, and the
sentence segmenter is a keyless-route component.

## The fix, and what it moved

`paths.extract_prompt(pack_name=None, root=None)`, forwarded at both call sites
(`extract_cmd.py`, and the `pack_prompt_path is None` fallback in
`llm_extractor.extract`). Three lines. Pinned by
`tests/test_extract_prompt_routing.py`, six tests, all six confirmed failing
against the pre-fix tree before the fix landed.

Both regression cases, same model, same corpus, same scorer:

| | detection | factor F1 | standards_reference | gate |
|---|---|---|---|---|
| nasa COU1 before | 13/19 | 0.839 | ASME-VV40-2018 | PASS |
| nasa COU1 after | **19/19** | **0.973** | NASA-STD-7009B | PASS |
| nasa COU2 before | 13/19 | 0.593 | ASME-VV40-2018 | **FAIL** |
| nasa COU2 after | **19/19** | **0.848** | NASA-STD-7009B | PASS |

And both corpus splits, tag `routing-fix-v1-llama33-70b` against
`absence-rule-v1-llama33-70b`, same model, same scorer:

| | dev before | dev after | test before | test after |
|---|---|---|---|---|
| mean factor F1 | 0.9035 | **0.9637** | 0.8909 | **0.9544** |
| vv40 half | 0.9686 | 0.9686 | 0.9652 | 0.9652 |
| nasa half | 0.8385 | **0.9588** | 0.8167 | **0.9436** |
| vv40 detection | 13/13 | 13/13 | 13/13 | 13/13 |
| nasa detection | 13/19 | **19/19** | 13/19 | **19/19** |
| factors at per-factor F1 0.000 | 6 of 19 | **none** | 6 of 19 | **none** |
| crashes | 0 | 0 | 0 | 0 |

Dev is 15 vv40 + 15 nasa bundles; test is 10 + 10, held out and sentinel-locked
(`--allow-test`).

**The vv40 half did not move at all** — same mean to four decimals on both
splits, same detection. It resolved to its own prompt before and after, so it is
the control on whether this run measures the fix or measures run-to-run
variation. It measures the fix.

## The other Phase 0 triage is the same bug

`studies/prompt-absence/FINDINGS.md` filed a separate pre-existing finding: **90
of 480 factors carry no status at all** — 71 whose ground truth is `assessed`
and 19 whose ground truth is `not_applicable` — and called it "a real gap in the
extract path ... worth its own investigation."

Those 90 are the six NASA-only factors across the 15 nasa dev bundles. Six times
fifteen is ninety, and the gold statuses of those ninety rows split 71 `assessed`
/ 19 `not_applicable`, matching that table's two numbers exactly. They had no
status because they had no row: the extractor was never asked about them.

Confirmed by the row count the groundedness scorer sees, which is the population
those 480 are drawn from:

    before   factors_total 390   (90 of 480 missing)
    after    factors_total 480   (0 missing)

So the ~19% incompleteness that the C2 completeness math inherits is not a
property of extraction. It resolves here, and it resolves to zero.

## What this does to H2 — and it is not good news for the metric

**COU2 was never a regression.** The only prior nasa-cou2 number, 0.848 from
2026-04-18, came from a different model (`ollama/qwen3.5:4b`), a different
prompt tag (`v3-nasa-aero`), and a *different scorer*: it predates `14822bd5`
(2026-08-06), which stopped crediting blank template rows as detections. Under
that older scorer the six blank rows counted as found. There is no arm of that
comparison that holds anything fixed.

**Part of the failing number was a scorer asymmetry, and it is worth recording
separately.** `_compute_f1` builds the gold set from `expected_status ==
"assessed"` only, while the predicted set is any row carrying content. COU2's
ground truth marks five factors `not-assessed`; the extractor reported all five
correctly as `not-assessed` — the report scores their *status* as correct — and
the F1 counted all five as **false positives**. Score the same output with those
five excluded from the predicted set and it is P 1.000 / R 0.571 / **F1 0.727**,
which clears the 0.70 gate. So the pass→fail transition was the artifact; the
six-factor hole underneath it was real. COU1 carries the identical hole and
**passed at 0.839**, because its ground truth happens to have no `not-assessed`
factors among the thirteen. The gate could not see the defect; it fired on the
case where an unrelated asymmetry happened to push the number down.

**And the metric is now demonstrably empty.** Post-fix, on both regression cases
and on both corpus splits, the extractor scores *exactly* the null control:

```
nasa COU1   candidate F1 0.973   best control 0.973   delta +0.000
nasa COU2   candidate F1 0.848   best control 0.848   delta +0.000
dev split   candidate F1 0.9637  best control 0.9637  delta +0.0000
test split  candidate F1 0.9544  best control 0.9544  delta +0.0000
```

This is stronger evidence for the H2 amendment than the finding it replaces.
"The null beats the extractor" invites the reply that the extractor is bad.
"Fixing the extractor's only detection defect makes it *identical* to a constant
that reads nothing" does not. Detection F1 on this corpus was measuring one
thing — whether the NASA factor block was present — and that thing was a routing
bug, not a property of extraction. With it fixed there is nothing left for the
metric to vary on: every factor is detected, which is what `control_constant_list`
does by construction.

**H2's per-factor condition is now a vacuous pass, and should be reported as
one.** The original criterion asks that per-factor F1 hold across the 19
factors. Post-fix it is exactly 1.000 for all nineteen, on both splits, with no
factor below. That is not nineteen passes; it is one fact — every factor in the
pack appears in every extraction — stated nineteen times, and a constant checklist
satisfies it identically. Every remaining failure in the corpus is a
`level_mismatch`: the extractor names the right factor and gets its level wrong.
Whatever signal is left in this scorer lives there, not in detection.

Both numbers stay in the record. The 0.9035 / 0.8909 dev/test figures were
measuring a bug on half the corpus, and that is the disclosure, not a footnote.

## Blast radius

- **vv40 was never affected** — it resolved to its own prompt, correctly, the
  whole time. Its per-factor F1 is 1.000 across all 13 on both splits before the
  fix. That makes it the control on the corpus re-run: vv40 numbers should not
  move.
- **`model-credibility` was affected; `iso42001`, `surrogate` and `disposition`
  were not.** Corrected 2026-08-15 — this section originally said all four ship
  an extract prompt and were subject to the resolver. Checked rather than
  assumed: only `model-credibility` has a `prompt` key in its manifest. The
  other three resolve to a directory that does not exist, so `build_prompt`
  finds nothing to send and `uofa extract` never reached them.

  `test_extract_prompt_routing.py` now covers all three prompt-bearing packs and
  pins that the other three resolve to no file — so if one of them gains a
  prompt later it has to join the parametrised list rather than shipping
  untested. It also adds a per-pack check that the delivered prompt defines that
  pack's own factors, since resolving inside `packs/<name>/` is necessary and
  not sufficient: a prompt could live in the right directory and still be a copy
  of another pack's.
- **Every shipped NASA-STD-7009B example and fixture** produced through this path
  carries a 13-factor extraction. The packaged examples under
  `packs/nasa-7009b/examples/` are hand-authored and unaffected, but any
  regenerated artifact is not.
- **Users** running `uofa extract --pack nasa-7009b` got a V&V 40 extraction in a
  NASA workbook, with no error and no warning.
- **The hosted Credibility Inspector was never affected**, even though it offers
  NASA-STD-7009B as a selectable standard and routes to it automatically.
  `space/pipeline.py:238` has its own `_prompt_path_for(pack)`, which resolves
  `pack_dir(pack)` and reads that pack's manifest — the correct logic, written
  out a second time.

  That is also why the bug survived. The path with a duplicate implementation was
  right; the shared helper everything else used was wrong, and nothing compared
  them. It is the same shape as the two sentence segmenters
  (`studies/shipped-segmenter/`), found in the same afternoon: a careful version
  living beside the one that actually ships. Now that `paths.extract_prompt`
  takes a pack, `_prompt_path_for` should call it rather than reimplement it —
  filed as follow-up, since changing the Space means a redeploy.

## What moved that is not detection

Reported because the re-run produces them, not because anything here should be
read as a result. Both metrics are the ones currently under investigation.

| | dev before | dev after | test before | test after |
|---|---|---|---|---|
| attribution rate | 0.6223 (234/376) | 0.5861 (262/447) | 0.5796 (142/245) | 0.6382 (187/293) |
| coverage | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_density | 0.208 | 0.188 | 0.192 | 0.216 |
| groundedness | 0.981 | 0.982 | 1.000 | 1.000 |

Attribution now scores more rows on both splits, because the rows exist. Its
**direction disagrees between the splits** — down 0.036 on dev, up 0.059 on test
— which is the clearest available warning against reading either as a result.
The measured property of this metric is that it tracks rationale length: a
20-sentence shotgun of random source sentences, filed identically under every
factor, scores 0.9284 against the extractor's 0.6383. The NASA factor rationales
are short. Whether these rows are genuinely worse-attributed or merely terser is
exactly the question Phase 1 exists to make answerable. Recorded here so the
numbers are not discovered later and read as a change in extraction quality.

Groundedness is stated as the triple throughout, never alone. At claim_density
0.19-0.22 a groundedness of 1.000 describes about a fifth of the output.

## Follow-up

1. Extend the routing test to `model-credibility`, `iso42001`, `surrogate`,
   `disposition` once their canonical factor lists are exported the way
   `VV40_FACTOR_NAMES` and `NASA_ALL_FACTOR_NAMES` are.
2. The scorer's assessed-only gold set versus content-bearing predicted set is a
   real asymmetry that penalises correct abstention. It belongs with the
   attribution-metric work rather than here, but it should not be left implicit:
   filed against Phase 1.
3. `docs/credibility-inspector.md` §7 quotes 0.8909 / 0.9035 as the figures the
   extraction hypothesis should be judged on, with no null control beside them.
   Corrected in the same change as this finding.

`studies/prompt-absence/FINDINGS.md` now carries a pointer here: its "separate
finding, pre-existing" section is answered by this one. Its own before/after
conclusions are unaffected — both its arms ran on the V&V 40 prompt, so nothing
between them is confounded — but the 480 it reports over is 390 real rows plus
90 that were never requested, and it now says so.
