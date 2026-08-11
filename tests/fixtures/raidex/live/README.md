# Live-run raidex fixtures

Records produced by running `raidex eval` here, as opposed to `../*.json` which
are verbatim published records from the cohort dataset. **Exact bytes, never
hand-edit** — same contract as the published fixtures.

They exist because a fresh raidex 0.1.4 record has a **different schema** from
the published cohort: it carries a `provenance` block the 43 published records
lack. Testing ingestion only against published records would leave the live path
unexercised, and the live path is the one that produces enterprise bundles.

## `together-llama-3.3-70b-limit150.json`

| | |
|---|---|
| Produced | 2026-08-11, raidex 0.1.4 |
| Command | `raidex eval --model together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo --tier A --judge <same> --limit 150` |
| Wall clock | 17m |
| Coverage | 7/9 (advglue, confaide are tier B) |
| Failures | 0 |

`--limit 150` matches how the published cohort was produced (its records show
`bbq n_samples` of 150 and 300). An unbounded run of the same tier is ~58k
prompts for `bbq` alone and takes hours — see docs/live-run-verification.md.

Two properties worth preserving:

- **`bbq` is the only constituent carrying an uncertainty**, exactly as in the
  published records. That the asymmetry reproduces on independently generated
  data is what makes W-AL-01's selectivity a property of the furnisher rather
  than an artifact of one dataset snapshot.
- **`provenance.datasets` pins all 7 benchmarks by revision hash**, and
  `provenance.sampling` records limit/concurrency/retries/timeout. The adapter
  does not yet read either; when it does, this fixture is what pins the change.
