# raidex furnisher fixtures

Verbatim records from [cloudronin/raidex-results](https://huggingface.co/datasets/cloudronin/raidex-results),
fetched 2026-08-10 from `resolve/main/`. **Exact bytes — never hand-edit.** These are the Group-B
extraction inputs for the `model-credibility` pack; editing one to make a test pass turns a real
furnisher property into a fiction, which is the failure the sufficiency layer exists to catch.

Refresh only by re-fetching from the dataset, and only deliberately — a record whose contents changed
upstream is a finding about raidex, not a fixture to quietly resync.

## What each fixture covers

| File | Coverage | HF card? | Why it is here |
|---|---|---|---|
| `anthropic__claude-sonnet-5.json` | 9/9 `full` | no | Firewall direction A: raidex evidence, no model card at all. Group A must give an honest no-card readout while Group B runs fully. |
| `huggingface__google__gemma-3-27b-it.json` | 9/9 `full` | yes (`google/gemma-3-27b-it`, API 200) | The both-sections case — the only fixture where Group A and Group B both populate. |
| `openai__gpt-5.6.json` | 8/9 `independent` | no | Constituent exclusion: `wmdp` has `value: null` and a populated `error`. Also the highest observed failure rate, `strongreject` at `n_failed: 45` of `n_samples: 268`. |
| `xai__grok-4.5.json` | 8/9 `independent` | no | Second exclusion case, so the adapter is not tuned to one record's shape. |

## Properties the adapter depends on, verified across all four

- **`bbq` is the only constituent carrying a real uncertainty estimate.** Its
  `raw.bbq_generate["acc_stderr,none"]` is a float in every record; all 8 other constituents have
  none. This asymmetry is the point — it is what makes W-EV-UQ-01 fire selectively instead of
  uniformly, and it must survive any refactor of the adapter.
- **`bbq` also carries 26 sub-scores whose stderr is the *string* `"N/A"`.** Only a float may populate
  `uncertaintyStatement`. `"N/A"`, `null`, and absent all mean absent (AGENTS.md §13: never emit a
  plausible value to satisfy a constraint).
- **`n_samples` is not constant** — observed 108, 150, 268, 300, 306, 312, 313, 445, 449, 450, 735,
  738. Nothing may assume 150.
- **An excluded constituent has `value: null`, `normalized: null`, and a populated `error`.** It must
  not become a `ValidationResult` with a null score; it is the composite-exclusion rule in the data,
  and the exclusion is what `rai_coverage` counts.
- **`badge` is a coverage tier, not a replication status** — `full` at 9/9, `independent` at 8/9. It
  carries no information about external replication. See correction 1 in the pack spec.

## Handling note: `error` strings contain absolute local paths

The `error` field on an excluded constituent is a raw harness traceback including the operator's
filesystem paths (`/Users/<name>/Documents/raidex-mono/backend/.venv/...`). The adapter must record
the exclusion as a short classification, **not** by copying the traceback into a bundle. Bundles from
this pack get published to uofa.net; verbatim copying would republish a third party's directory
structure to a public site.
