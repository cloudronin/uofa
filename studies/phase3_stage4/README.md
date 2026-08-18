# Stage 4: gap-probe grounding

One question, arising from the Stage 4 author adjudication:

> Do the ensemble's REAL-GAP verdicts on gap_probe cases rest on the package,
> or on the prompt header?

## Why it is worth asking

The production judge rubric (`packs/core/judge_prompts/v1.1.0.md`) sets REAL-GAP as:

> `coverage_intent = gap_probe` AND the package content **visibly instantiates
> the §6.7 candidate's defeater** AND either no rules fired, or the rules that
> fired are semantically distinct

The middle condition presumes a named candidate exists. Measured over the
bundle, **210 of 330** gap_probe cases carry a source taxonomy that maps to none
of the six §6.7 Tier-1 candidates. For those the condition has no referent, and
a judge would have to supply the defeater unaided — which is the expert prior
the catalog exists to codify.

This matters because 289 REAL-GAP verdicts underpin the 6-of-6 Tier-1 result.
If a large share of them were reachable from the prompt header alone, that is a
finding about the Tier-1 claim rather than about any single case.

## Method

For each judgment, split the vocabulary the judge could have drawn on:

- **header pool** — case_id, coverage_class, source_taxonomy,
  expected_target_rule, rules_fired: everything the prompt handed it
- **package pool** — tokens appearing in the package JSON-LD and *not* in the
  header pool

Then count how many package-distinctive tokens the judge's `instantiation_check`
echoes. Reasoning grounded in the artifact reuses factor names, validation-result
names, quoted criteria. Reasoning resting on the frame reuses header terms and
generic verdict vocabulary only.

Deliberately **not** a keyword regex. INV-17 recorded two traps from that
approach — a narrow pattern silently killing multi-word markers, and `re.X`
eating spaces — and the same class of error recurred by hand during the Stage 4
adjudication, on a case whose content was plainly present. Token overlap has no
pattern to get wrong, and every exclusion is logged rather than dropped.

## Running it

```bash
python studies/phase3_stage4/check_gap_probe_grounding.py --finished
```

The flag is a speed bump, not a lock. This reads judge verdicts and reasoning,
which `ADJUDICATION_INSTRUCTIONS.md` reserves until the Stage 4 worksheet is
finished — reading them early contaminates the author-versus-judge agreement
statistic the worksheet exists to produce.

## Reading the output

Three blocks: all gap_probe judgments, REAL-GAP where the probe pointed at a
Tier-1 candidate, and REAL-GAP where it pointed at none. Read the last one
first. A high zero-echo share there means those verdicts did not need the
package.

Per-judgment detail lands in
`dev/build/adversarial/phase3/adjudication/gap_probe_grounding.csv`.

## Note on the ensemble

The three judges are not interchangeable: A is `gpt-5.4`, B is
`gemini-2.5-pro`, C is `Llama-4-Maverick-17B-128E-Instruct`. Whether a bare
taxonomy slug like `gohar/contextual/faults-software` evokes the defeater is a
question about model priors, so results are reported per judge rather than
pooled. Judge C's records also carry two different model identifiers
(`Llama-4-Maverick-17B-128E-Instruct` on 1,180 and `meta-llama/llama-4-maverick`
on 3,739), which is worth confirming is one model before treating C as one judge.

Duplicate judgments exist from retries and resumes (549 in A, 79 in B, 363 in C
against 4,556 distinct cases each). The script keeps the first per
(judge, case_id) and logs the count rather than double-counting.
