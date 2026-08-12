# The pack rename, and why these study records were not rewritten

**2026-08-12.** `packs/mrm-nist` became `packs/model-credibility` (Phase 7).

Every file under `studies/` was **deliberately excluded** from the rename.

## Why

These are committed measurement records. Their pins state **what was read at
measurement time**:

```json
"prompt_file": "packs/mrm-nist/prompts/card_eval_extract_prompt.txt",
"prompt_sha256": "faacd0f9cea62dfa"
```

That path is where the prompt lived when those extractions ran. Rewriting it to
`packs/model-credibility/...` would make the record assert that a run read a path
which did not exist on the day it ran — falsifying a provenance claim to make it
tidy. A pin that is updated to stay convenient is not a pin.

The same applies to prose in `CONSTRUCT-DRIFT.md`, `PROMPT-V2-FORK.md` and the
rest: they describe what the artifacts were called while the work happened.

## How to read a study pin after the rename

`packs/mrm-nist/<path>` in a study record means `packs/model-credibility/<path>`
today. The `prompt_sha256` beside it is the authoritative identifier — content
hashes survive renames, which is the point of having them.

## Live configuration WAS renamed

Code, packs, docs, site content and tests all moved. Only the historical record
stayed. A `mrm-nist` reference in `src/` would be a bug; a `mrm-nist` reference
in `studies/` is the record doing its job.

`paths.PACK_ALIASES` keeps `--pack mrm-nist` and pre-rename bundles resolving for
one version.
