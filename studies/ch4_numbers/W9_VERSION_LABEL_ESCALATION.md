# W9 — version-label sweep: triage, escalated, no edits made

W9 of the Ch4 Numbers and Repairs spec. The spec budgeted 30 minutes for a
disambiguation sweep. Triage first, per instruction, and the result is that
**this should not be edited through in one pass**.

**64 bare `v0.6` / `v0.7` occurrences across 20 files.** No edits have been made.

## Why it escalates rather than proceeds

Two reasons, either sufficient on its own.

**Most of the volume is a different version line.** `docs/vocabulary-status.md`
(15) and `docs/vocabulary-cleanup-audit.md` (8) are about the **vocabulary/pack**
line, where the core pack is genuinely at 0.6.0. Rewriting those to
"catalog v0.6 (following v0.5.15.1)" would not disambiguate them — it would make
them **wrong**. The spec's own instruction anticipated this hazard for one
filename; it turns out to be the majority of the corpus.

**Fourteen occurrences sit in decision or spec documents.** Those carry rulings.
Disambiguating a version reference inside a ruling changes what the ruling says
it applies to, which is an author call rather than a mechanical edit.

## The full touch list

### A. Decision / spec documents — author review required (14)

| File | n | Note |
|---|---:|---|
| `docs/UofA_Unified_Repair_Spec_v2_1.md` | 7 | ruling 5 defers `sh:in` "to v0.6"; several descendants inherit it |
| `docs/UofA_Ch4_Numbers_and_Repairs_Spec_v1_0.md` | 4 | R3, and the "v0.6 catalog increment" phrasing |
| `docs/UofA_Decision_Record_2026-08-16.md` | 3 | ruling 5 and ruling 11 — **the record itself; edits here are ESCALATION by spec §5.6** |

### B. Vocabulary / pack line — do **not** rewrite as catalog (29)

| File | n |
|---|---:|
| `docs/vocabulary-status.md` | 15 |
| `docs/vocabulary-cleanup-audit.md` | 8 |
| `docs/vocabulary-authoring-spec.md` | 3 |
| `docs/vocabulary-cli-wiring-spec.md` | 3 |

These track the vocabulary's own version. If anything is ambiguous here it is the
*reverse* problem — a reader arriving from the catalog line may misread them —
which is fixed by a one-line scope note at the top of each, not by renumbering.

### C. Everything else (21)

| File | n | Likely line |
|---|---:|---|
| `CHANGELOG.md` | 3 | unreleased section — mixed |
| `docs/investigations/INV-8-findings.md` | 3 | catalog increment |
| `docs/UofA_Phase2_5a_Spec_v1_3.md` | 2 | catalog |
| `docs/UofA_Ruling_Implementation_Plan_2026-08-16.md` | 2 | catalog |
| `docs/v0.5-morrison-deltas.md` | 2 | catalog |
| `PHASE3_STATUS_REPORT.md` | 2 | catalog |
| `docs/investigations/SUMMARY.md`, `INV-4-findings.md`, `INV-6-findings.md` | 1 each | catalog |
| `docs/UofA_Argument_Layer_Spec_v0_1.md` | 1 | post-defense schema increment |
| `docs/valid-package-spec.md` | 1 | schema |
| `README.md` | 1 | needs reading in context |
| `docs/model-credibility-pack-addendum-v0_6-field-study.md` | 1 | **pack line, in the filename** — do not renumber |

## Recommended disposition

1. **Group B gets a scope note, not a rewrite** — one line at the top of each of
   the four vocabulary documents naming which version line they track. Four small
   edits, no renumbering, and it fixes the ambiguity in the direction it actually
   runs.
2. **Group A is read by the author**, since each occurrence sits inside a ruling.
   The Decision Record is a frozen artifact under spec §5.6 in any case.
3. **Group C is mechanical** once A and B are settled — apply "the post-defense
   schema increment" in manuscript-bound text and "catalog v0.6 (following
   v0.5.15.1)" where a number is required, with the two named exceptions left
   alone.

Nothing in this file has been applied. Re-derive the counts with:

```bash
/Users/vishnu/miniconda3/bin/python -c "
import re,pathlib,collections
B=re.compile(r'(?<![\w.])v0\.[67](?![\w.\d])')
c=collections.Counter()
for p in list(pathlib.Path('docs').rglob('*.md'))+list(pathlib.Path('.').glob('*.md')):
    n=len(B.findall(p.read_text(encoding='utf-8')))
    if n: c[str(p)]=n
print(sum(c.values()),'occurrences across',len(c),'files')"
```
