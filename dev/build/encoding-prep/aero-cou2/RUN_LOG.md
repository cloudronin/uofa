# Run log — aero cou2 encoding prep

State: **DRAFT, AWAITING-AUTHOR.** Prepared under `docs/Encoding_Protocol_v0_1_DRAFT.md`.
Nothing signed. The §3b cell walk has not occurred; anchors below are candidates.

## Pins

| What | Value |
|---|---|
| model | `claude-sonnet-5` |
| backend | `anthropic` (litellm provider path) |
| thinking mode | off |
| max_tokens | 16384 (extractor default) |
| prompt sha256 (first 16) | `c47bf1745a12084e` |
| site commit | `31cb466` |
| repo HEAD | `517abad` |
| base_uri | `https://github.com/cloudronin/uofa` [AUTHOR-CONFIRM before signing] |
| pack | nasa-7009b 0.5.0 |
| source | `aero-evidence-cou2/`, synthetic bundle, source class declared per §2a |

## Extractor lineage, per §1e

The extractor is `anthropic/claude-sonnet-5`. It is **not** the model the extraction eval
used; that eval ran on local `ollama/qwen3.5:4b`. It is not the model-selection scorecard's
arm 4 either, though that arm names the same string, because the scorecard is a different
study. Lineage is declared here rather than inherited.

## Source class, per §2a

Synthetic evidence bundle, committed at `packs/nasa-7009b/examples/aerospace/aero-evidence-cou2.zip`.
Admissible: the protocol governs process rather than source authenticity.

## Review state

Anchors are **candidates authored from EVIDENCE_MANIFEST.txt**, not derived from extractor
provenance. The extractor records no per-cell source document; the cell comments carry a
confidence percentage only, although the published on-ramp says "Hover a cell for the
document it came from". The author's walk confirms or corrects each one.
