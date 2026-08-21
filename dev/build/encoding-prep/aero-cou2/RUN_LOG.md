# Run log — aero cou2 encoding prep

State: **ADJUDICATED AND SIGNED, 2026-08-21.** The author assented to
`AUTHOR_SUMMARY_COU2.md`, which is the review act, and signed the package. All dispositions
and ambiguity entries carry the author's rulings. Originally prepared under `docs/Encoding_Protocol_v0_1_DRAFT.md`.
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

---

## Cell walk and re-import — 2026-08-21

Mechanical resolution against the author-committed, pre-registered ground truth
`tests/fixtures/extract/ground_truth/aero-cou2-nasa7009b.json`, plus the author's Johnson
rulings as precedent. **Machine acts, recorded as machine acts.** The author's review act is
assent to `AUTHOR_SUMMARY_COU2.md`; nothing below is an author adjudication.

| Field | Value |
|---|---|
| Performed by | Claude Code, apply session |
| Date | 2026-08-21 |
| Script | `dev/build/encoding-prep/aero_cell_walk.py`, idempotent; re-running reproduces the ledger byte for byte |
| Pre-walk snapshot | `pre-walk/aero-cou2-extracted-PREWALK.xlsx`, so the walk's changes stay measurable the way `raw-extract/` makes the prep's measurable |
| Ledger | `REVIEW_LEDGER.md` |
| Dispositions | `DISPOSITIONS_DRAFT.md` — drafted here, **all verdicts ruled by the author 2026-08-21**; no AUTHOR-RULE rows remain |
| Author summary | `AUTHOR_SUMMARY_COU2.md` |

### Re-import

    UOFA_ASSESSOR="Vishnu Vettrivel" uofa import aero-cou2-extracted.xlsx \
      --pack nasa-7009b --base-uri https://github.com/cloudronin/uofa --protocol-check

`UOFA_ASSESSOR` is set **explicitly**, so `wasAttributedTo` is a declared operator rather than
one inherited from whatever shell the import ran in. That is not yet a protocol requirement —
it is queued for v0.2 in `docs/protocol-v0_2-notes.md` — but the Johnson package was signed
carrying an inherited container identity and had to be re-imported and re-signed to fix it.
Doing it here costs nothing and avoids repeating a known defect knowingly.

`--protocol-check`: **9 of 9 green.** `uofa check`: C2 SHACL pass, C3 Rules pass, **C1 Integrity
fails correctly** on the importer's zero-filled placeholders, which is the unsigned state and
Johnson finding F-6d's condition rather than a defect.

**Not performed:** signing, ledger-row changes, and the public-wheel round-trip. The last is
flagged in the summary rather than claimed, because no wheel is built in this tree.

### Sign-off — completed 2026-08-21

| Field | Value |
|---|---|
| Review act | author's **assent to `AUTHOR_SUMMARY_COU2.md`**, whose §1 correction list is what the assent covers |
| Signed by | **Vishnu Vettrivel**, author, with `~/.config/uofa/research.key` |
| `signatureAlg` / `canonicalizationAlg` | `ed25519` / `json-sortkeys/v1` |
| `signature` | `ed25519:c6627e798f751c7c…4f0080b` |
| `hash` | `sha256:ad3e4e8bddd837313199a0bb7791b5b021dec8e0bebfbedf211362480270e8f5` |

**Local verification:** `uofa check --pack nasa-7009b` → **C1 Integrity ✓ · C2 SHACL ✓ · C3 Rules ✓.**

**Public-wheel round-trip: PERFORMED and green.** A clean virtualenv with the published
`uofa==0.12.0` from PyPI, the package copied **outside the repository** so nothing resolves
from the working tree, returns C1 ✓ C2 ✓ C3 ✓. The wheel bundles the packs and the Jena rule
engine, so this exercises all three gates rather than the signature alone.

This is a genuine **cross-version** check, which is the part worth keeping: the package was
imported under the pinned `uofa-cli 0.11.0` and verifies under the published 0.12.0. A
signature that holds across that gap is the claim a reference encoding actually has to support,
and it is the claim an outside verifier will test.

**Nothing about this package is outstanding.** The encoding is complete, adjudicated, signed
and independently verified.
