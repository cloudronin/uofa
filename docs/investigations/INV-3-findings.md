# INV-3 — Morrison COU1 last-touch date (washout clock for A8)

Status: **CLOSED — one wording question raised by parent spec v2.0**
Date: 2026-08-16 (addendum same day, against `UofA_Unified_Repair_Spec_v2_0.md`)
Feeds: parent A8 (optional, only if elected)

---

# ADDENDUM — re-investigated against parent spec v2.0

**v2.0 §A8 says "minimum 3-week washout from last package touch."** This finding
recommends dating from the last **material** touch (`5331ba4c`, 2026-08-06 →
washout ends **2026-08-27**). Read literally, "last package touch" is the last
touch of any kind, which is `09d19eeb` (2026-08-13, the key-rotation re-sign) →
washout ends **2026-09-03**.

The one-line difference is worth resolving deliberately rather than by which word
the spec happened to use, because the two readings differ by a week and A8 is
calendar-contingent. The case for 2026-08-06: the re-sign changed one `signature`
line and touched no encoding content or disposition, so it cannot have refreshed
the author's memory of the encoding — verified by reading the diff. The case for
2026-08-13: A8's purpose is memory decay, and "I handled this file" is a weak but
real exposure. **This is the same question as re-exposure event R1 in the original
finding, and the spec's wording does not settle it.**

Two other v2.0 clauses bear on A8's feasibility:

1. **A8 forbids access to the "prior package/notes/ambiguity log" until the
   re-encode is committed.** There is no ambiguity log, because A7 is unwritten
   (INV-2). So A8 cannot run before A7 lands — a dependency v2.0's ordering table
   already implies ("Optional, post-washout") but does not state.
2. **A8's thresholds are now pre-committed**: JUDGMENT disposition raw agreement
   ≥0.85; MECHANICAL agreement below ~1.0 is itself a reportable defect. That is
   INV-4's requirement input and is recorded there.

No change to the commit table or the classification.

---

# ORIGINAL FINDING (v1.1-based, retained for the record)

## Recommendation

**Washout starts 2026-08-06.** Three weeks from the last material touch puts the
earliest blind re-encode date at **2026-08-27**.

That date is driven by one commit, `5331ba4c`, which rewrote the Morrison COU1
*ground-truth encoding* — not by any of the more recent commits that touch Morrison
files, all of which are incidental.

Two re-exposure events are flagged below for the author to rule on; if either
counts, the clock moves to **2026-08-13** (→ 2026-09-03).

## Artifacts in the Morrison COU1 family

Found by searching Morrison/COU1 identifiers repo-wide, not by following the
fixture's own log.

| Artifact | Role |
|---|---|
| `tests/fixtures/extract/ground_truth/morrison-cou1.json` | the encoding under test — factor-level ground truth |
| `packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld` | the signed example package |
| `packs/vv40/examples/morrison/source/` | source documents (PDF/CSV/DOCX + `EVIDENCE_MANIFEST.txt`) |
| `tests/fixtures/extract_corpus_vv40/bundle_morrison/{ground_truth,metadata}.json` | extract-eval bundle |
| `dev/specs/negative_controls/nc-clean-{full,minimal}-morrison-cou1.yaml` | adversarial NC specs pinned to this COU |
| `tests/space/fixtures/morrison_cou1_{state.json,reviewer.html}` | Space UI fixtures |
| `tests/fixtures/report_goldens/morrison_vv40.{json,text,markdown}` | report golden files |
| `packs/vv40/examples/morrison/slide-assets/cou1-*.txt`, `*.png` | presentation exports |
| `docs/v0.5-morrison-deltas.md` | version-delta notes |

## Commit table

### `tests/fixtures/extract/ground_truth/morrison-cou1.json` (`git log --follow`)

| Commit | Date | Subject | Class | Why |
|---|---|---|---|---|
| `5331ba4c` | **2026-08-06 15:35:54 −0700** | feat(fixtures): transcribe Morrison's selected goals, and flag what will not reconcile | **MATERIAL** | +194/−? lines across `morrison-cou1.json`; the commit's own subject says it transcribes selected goals and records irreconcilable items. This is content of the encoding. |
| `673d60f6` | 2026-04-05 16:33:45 −0700 | feat: prompt engineering for vv40 extract command | MATERIAL (superseded) | Original creation of the fixture. |

### `packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld`

| Commit | Date | Subject | Class | Evidence |
|---|---|---|---|---|
| `09d19eeb` | 2026-08-13 11:31:46 −0700 | sec: rotate the leaked research signing key and re-sign all artifacts (#55) | **INCIDENTAL** | Diff is exactly one line: `signature` value replaced. No content field touched. |
| `316daf6f` | 2026-05-31 08:12:47 −0700 | fix(integrity): relabel canonicalizationAlg to the truthful json-sortkeys/v1 | **INCIDENTAL** | Diff is exactly one line: `canonicalizationAlg` string relabelled `RDFC-1.0` → `json-sortkeys/v1`. A truthfulness fix to a metadata label. |
| `5d75b48e` | 2026-04-28 05:14:34 −0700 | phase2_5 v0.5.11: W-AR-02 offset-rationale predicate refinement + NC corpus regen | **INCIDENTAL for COU1** | Diff to Morrison COU1 is 4 lines: `hash` + `signature` only. The substantive `hasOffsetRationale` insertion in this commit went to **Nagaraja COU1** (12 lines), not Morrison. Worth stating explicitly because the file appears in the commit's stat and looks material until the diff is read. |
| `49b92636` | 2026-04-21 03:08:04 −0700 | fix(tests): CI regression cleanup after v0.5.0 release | INCIDENTAL | |
| `4322c865` | 2026-04-21 00:10:15 −0700 | feat(schema): v0.5 JSON-LD context + SHACL scaffolding | INCIDENTAL (schema migration) | |
| `992955ac` | 2026-04-04 23:41:57 −0700 | refactor: move examples and templates under pack directories | INCIDENTAL (path move) | |

**Latest material touch across the family: `5331ba4c`, 2026-08-06.**

## Re-exposure events — flagged for author ruling

The item asks whether the Inspector demo or any recent study re-used the COU1
package in a way that constitutes re-exposure. Two candidates, reported separately
rather than folded into the clock:

| Event | Date | What happened | Why it might count |
|---|---|---|---|
| **R1 — key rotation re-sign** | 2026-08-13 (`09d19eeb`) | Every signed artifact, including Morrison COU1, was re-signed after a leaked research key. | The *file* changed and was necessarily opened by tooling. Content was not read or judged. Argument for not counting: no encoding decision was revisited. Argument for counting: the author handled the package 7 days after the material touch. |
| **R2 — Space demo bundled sample** | ongoing | `morrison-sample` is a bundled sample in the Credibility Inspector, and `tests/space/fixtures/morrison_cou1_{state.json,reviewer.html}` are checked-in renders of the COU1 analysis. Any demo run or UI test displays the COU1 factor statuses. | The blind re-encode's premise is that the author has not recently seen COU1's encoded factor dispositions. The reviewer HTML fixture displays exactly those. **This is the stronger of the two.** |

If R2 counts, the washout should start from the author's most recent demo run
rather than from a commit — a date only the author can supply. If R1 counts, the
clock starts 2026-08-13 → **2026-09-03**.

**No escalation.** The material/incidental call was unambiguous for every commit:
each incidental one was verified by reading its actual diff on the Morrison COU1
file, and every such diff was confined to `hash`, `signature`, or
`canonicalizationAlg`. No commit sits near the boundary in a way that would move
the date by more than a few days on its own. The only genuine open question is R1/R2,
which is an author judgment about exposure, not a classification of a commit.

## Coverage statement

**Searched.** `git log --follow --format='%h|%ci|%an|%s'` on
`tests/fixtures/extract/ground_truth/morrison-cou1.json`. `git log` on
`packs/vv40/examples/morrison/cou1/`. `git show <commit> -- <path>` on `09d19eeb`,
`316daf6f`, `5d75b48e` to read the actual diffs rather than trusting subjects.
`git show --stat` on `5331ba4c` and `5d75b48e`. Repo-wide `find -ipath "*morrison*"`
and case-insensitive grep for `morrison` across `*.json`, `*.jsonld`, `*.md`,
`*.py`, `*.yaml`, `*.csv` to build the artifact family independently of the
fixture's own log.

**NOT searched.**
- **`docs/v1/annot_morrison.json` and `docs/v1/valresults_morrison.json`** were
  found but their histories were not pulled. They look like v0.1-era artifacts
  predating the current encoding; if either is a live disposition record, its log
  should be checked before the clock is fixed. Low risk, cheap to close.
- Ambiguity logs and disposition records **as a distinct artifact class do not
  exist in this repo** — there is no encoding-protocol ambiguity log, because A7 is
  unwritten (see INV-2). So "every artifact co-evolving with the encoding" is,
  today, only the fixture plus the example package. That absence is itself worth
  recording in A4.
- Author-side exposure outside git (reading the PDF sources, running the demo, the
  slide assets in `packs/vv40/examples/morrison/slide-assets/`) is unknowable from
  the repo. R2 above is the visible tip of it.
- The `nagaraja` and NASA HPT anchors were not dated; only Morrison COU1 was in
  scope.
