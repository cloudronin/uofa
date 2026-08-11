# Model-card fixtures

Verbatim HF model cards used as test inputs. **Exact bytes, never hand-edit** —
the point is that a real card exercises the extractor, and an edited one stops
being evidence about anything.

These live here rather than in `packs/mrm-nist/examples/` because the pack
examples are *curated* artifacts: each carries human-read factor statuses in
`curated_cards.py`. A card needed only as raw text for a render test is a test
fixture, not a curated demo.

## `google__gemma-3-27b-it.md`

| | |
|---|---|
| Model | `google/gemma-3-27b-it` |
| Fetched | 2026-08-11 |
| Repo sha | `005ad3404e59d6023443cb575daa05336842228a` |
| README blob oid | `fdce721ee5de878029a086bcc7f6cd7f183fab32` |
| Size | 25,123 bytes / 2,971 words |

Chosen because it is **the only open-weight model with both a published card and
a raidex record** (the cohort is 41/43 hosted endpoints). That makes it the one
subject where sections [1] and [3] of a report describe the same model, so the
report goldens stopped pairing one model's card with another's scores.

`*.pin.json` records both hashes deliberately, and they differ. The repo sha
moves when **any** file in the repo changes, so pinning it marks a byte-identical
card stale on a weights re-upload; the README blob oid is what an A9.1 artifact
pin must record. Phase 6 implements that, and this fixture is what pins it.
